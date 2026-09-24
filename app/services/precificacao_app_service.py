from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app import db
from app.models.feedback_cliente import FeedbackCliente
from app.models.historico_preco import HistoricoPreco
from app.models.preco_concorrente import PrecoConcorrente
from app.models.sugestao_preco import SugestaoPreco
from app.repositories.preco_concorrente_repository import PrecoConcorrenteRepository
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.sugestao_preco_repository import SugestaoPrecoRepository
from app.repositories.venda_repository import VendaRepository


class PrecificacaoAppService:
    def __init__(self):
        self.produtos = ProdutoRepository()
        self.vendas = VendaRepository()
        self.concorrentes = PrecoConcorrenteRepository()
        self.sugestoes = SugestaoPrecoRepository()

    def registrar_preco_concorrente(self, id_produto, valor):
        if not self.produtos.buscar_por_id(id_produto):
            raise ValueError("Produto não encontrado.")
        valor = Decimal(str(valor))
        if valor <= 0:
            raise ValueError("O preço do concorrente deve ser maior que zero.")
        return self.concorrentes.adicionar(
            PrecoConcorrente(id_produto=id_produto, valor=valor)
        )

    def registrar_feedback(self, id_produto, comentario, cliente=None):
        if not self.produtos.buscar_por_id(id_produto):
            raise ValueError("Produto não encontrado.")
        if not comentario or not comentario.strip():
            raise ValueError("O comentário do cliente é obrigatório.")
        feedback = FeedbackCliente(
            id_produto=id_produto, comentario=comentario.strip(), cliente=cliente
        )
        db.session.add(feedback)
        db.session.commit()
        return feedback

    def gerar_sugestao(self, id_produto, solicitante_id=None, feedback_cliente=None):
        produto = self.produtos.buscar_por_id(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")

        giro = Decimal(str(self.vendas.total_vendido(id_produto, 30)))
        concorrente = self.concorrentes.ultimo_por_produto(id_produto)
        preco_concorrente = Decimal(str(concorrente.valor)) if concorrente else None
        motivos = []
        preco = Decimal(str(produto.preco_atual))

        if giro < Decimal("10"):
            preco *= Decimal("0.95")
            motivos.append("giro baixo nos últimos 30 dias")
        if produto.data_validade and produto.data_validade <= (
            datetime.utcnow().date() + timedelta(days=7)
        ):
            preco *= Decimal("0.90")
            motivos.append("validade próxima")
        if preco_concorrente and preco > preco_concorrente:
            preco = min(preco, preco_concorrente * Decimal("0.98"))
            motivos.append("preço acima do concorrente")
        if feedback_cliente:
            motivos.append("feedback de cliente")
        if not motivos:
            motivos.append("revisão preventiva de preço")

        preco = max(preco, Decimal(str(produto.custo)) * Decimal("1.05"))
        preco = preco.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sugestao = SugestaoPreco(
            id_produto=id_produto,
            id_solicitante=solicitante_id,
            preco_atual=produto.preco_atual,
            preco_sugerido=preco,
            giro_30_dias=giro,
            preco_concorrente=preco_concorrente,
            motivo="; ".join(motivos),
            feedback_cliente=feedback_cliente,
        )
        return self.sugestoes.adicionar(sugestao)

    def listar_pendentes(self):
        return self.sugestoes.pendentes()

    def decidir_sugestao(
        self, id_sugestao, decisao, aprovador_id, preco=None, observacao=None
    ):
        sugestao = self.sugestoes.buscar_por_id(id_sugestao)
        if not sugestao:
            raise ValueError("Sugestão não encontrada.")
        if sugestao.status != "PENDENTE":
            raise ValueError("A sugestão já foi decidida.")
        decisao = decisao.upper()
        if decisao not in {"APROVADA", "EDITADA", "REJEITADA"}:
            raise ValueError("decisao deve ser APROVADA, EDITADA ou REJEITADA.")
        if decisao == "EDITADA":
            if preco is None or Decimal(str(preco)) <= 0:
                raise ValueError("Informe um preço válido para uma sugestão editada.")
            sugestao.preco_sugerido = Decimal(str(preco))
        if decisao in {"APROVADA", "EDITADA"}:
            produto = self.produtos.buscar_por_id(sugestao.id_produto)
            preco_antigo = produto.preco_atual
            produto.preco_atual = sugestao.preco_sugerido
            db.session.add(
                HistoricoPreco(
                    id_produto=produto.id_produto,
                    preco_antigo=preco_antigo,
                    preco_novo=sugestao.preco_sugerido,
                    motivo=f"Sugestão de preço #{sugestao.id_sugestao} {decisao.lower()}",
                )
            )
        sugestao.status = decisao
        sugestao.id_aprovador = aprovador_id
        sugestao.observacao_aprovacao = observacao
        sugestao.data_decisao = datetime.utcnow()
        self.sugestoes.salvar()
        return sugestao
