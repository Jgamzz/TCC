from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func

from app import db
from app.models.configuracao_regras import ConfiguracaoRegras
from app.models.feedback_cliente import FeedbackCliente
from app.models.historico_preco import HistoricoPreco
from app.models.preco_concorrente import PrecoConcorrente
from app.models.sugestao_preco import SugestaoPreco
from app.models.venda import Venda
from app.repositories.preco_concorrente_repository import PrecoConcorrenteRepository
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.sugestao_preco_repository import SugestaoPrecoRepository
from app.repositories.venda_repository import VendaRepository
from app.services.auditoria_service import registrar_auditoria


class PrecificacaoAppService:
    def __init__(self):
        self.produtos = ProdutoRepository()
        self.vendas = VendaRepository()
        self.concorrentes = PrecoConcorrenteRepository()
        self.sugestoes = SugestaoPrecoRepository()

    def obter_configuracao(self):
        configuracao = db.session.get(ConfiguracaoRegras, 1)
        if not configuracao:
            configuracao = ConfiguracaoRegras(
                id_configuracao=1,
                limiar_giro=10,
                dias_validade=7,
                margem_minima=15,
            )
            db.session.add(configuracao)
            db.session.commit()
        return configuracao

    def salvar_configuracao(self, dados, usuario_id):
        if not isinstance(dados, dict):
            raise ValueError("Os parâmetros precisam ser um objeto JSON.")
        try:
            margem = Decimal(str(dados["margem_minima"]))
            giro = Decimal(str(dados["limiar_giro"]))
            dias = int(dados["dias_validade"])
        except (KeyError, ArithmeticError, TypeError, ValueError):
            raise ValueError("Informe margem, limiar de giro e dias válidos.") from None
        if (
                not margem.is_finite()
                or not giro.is_finite()
                or margem < 0
                or margem > 100
                or giro < 0
                or dias < 1
                or dias > 3650
        ):
            raise ValueError("Os parâmetros informados estão fora dos limites permitidos.")
        configuracao = self.obter_configuracao()
        configuracao.margem_minima = margem
        configuracao.limiar_giro = giro
        configuracao.dias_validade = dias
        registrar_auditoria(
            "CONFIGURACAO_ATUALIZADA",
            "ConfiguracaoRegras",
            usuario_id=usuario_id,
            entidade_id=1,
            detalhes={
                "margem_minima": str(margem),
                "limiar_giro": str(giro),
                "dias_validade": dias,
            },
        )
        db.session.commit()
        return configuracao

    def registrar_preco_concorrente(self, id_produto, valor, concorrente=None, usuario_id=None):
        if not self.produtos.buscar_por_id(id_produto):
            raise ValueError("Produto não encontrado.")
        try:
            valor = Decimal(str(valor))
        except (ArithmeticError, TypeError, ValueError):
            raise ValueError("O preço do concorrente deve ser numérico.") from None
        if not valor.is_finite() or valor <= 0:
            raise ValueError("O preço do concorrente deve ser maior que zero.")
        concorrente = str(concorrente or "").strip()
        if not concorrente:
            raise ValueError("Informe o nome do concorrente.")
        preco = PrecoConcorrente(
            id_produto=id_produto,
            valor=valor,
            concorrente=concorrente[:120],
        )
        db.session.add(preco)
        db.session.flush()
        registrar_auditoria(
            "PRECO_CONCORRENTE_REGISTRADO",
            "PrecoConcorrente",
            usuario_id=usuario_id,
            entidade_id=preco.id_preco_concorrente,
            detalhes={
                "id_produto": id_produto,
                "concorrente": concorrente,
                "preco": str(valor),
            },
        )
        db.session.commit()
        return preco

    def registrar_feedback(self, id_produto, comentario, cliente=None, usuario_id=None):
        if not self.produtos.buscar_por_id(id_produto):
            raise ValueError("Produto não encontrado.")
        if not isinstance(comentario, str) or not comentario.strip():
            raise ValueError("O comentário do cliente é obrigatório.")
        feedback = FeedbackCliente(
            id_produto=id_produto, comentario=comentario.strip(), cliente=cliente
        )
        db.session.add(feedback)
        db.session.flush()
        registrar_auditoria(
            "FEEDBACK_REGISTRADO",
            "FeedbackCliente",
            usuario_id=usuario_id,
            entidade_id=feedback.id_feedback,
            detalhes={"id_produto": id_produto},
        )
        db.session.commit()
        return feedback

    def gerar_sugestao(self, id_produto, solicitante_id=None, feedback_cliente=None):
        produto = self.produtos.buscar_por_id(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")

        giro = Decimal(str(self.vendas.total_vendido(id_produto, 30)))
        concorrente = self.concorrentes.ultimo_por_produto(id_produto)
        preco_concorrente = Decimal(str(concorrente.valor)) if concorrente else None
        configuracao = self.obter_configuracao()
        return self._montar_sugestao(
            produto,
            giro,
            preco_concorrente,
            solicitante_id,
            feedback_cliente,
            persistir=True,
            configuracao=configuracao,
        )

    def consultar_giro_catalogo(self):
        produtos = self.produtos.listar()
        totais = self.vendas.totais_por_produto(
            [produto.id_produto for produto in produtos]
        )
        return [
            {
                "id_produto": produto.id_produto,
                "produto": produto.nome,
                "estoque_atual": float(produto.estoque),
                "quantidade_vendida_7_dias": totais.get(
                    produto.id_produto, (0.0, 0.0)
                )[0],
                "quantidade_vendida_30_dias": totais.get(
                    produto.id_produto, (0.0, 0.0)
                )[1],
            }
            for produto in produtos
        ]

    def gerar_sugestoes_catalogo(self, solicitante_id):
        produtos = self.produtos.listar()
        if len(produtos) > 500:
            raise ValueError("A geração em lote aceita até 500 produtos ativos.")
        if not produtos:
            return []
        configuracao = self.obter_configuracao()
        ids = [produto.id_produto for produto in produtos]
        agora = datetime.utcnow()
        inicio = agora - timedelta(days=30)
        giros = dict(
            db.session.query(Venda.id_produto, func.sum(Venda.quantidade))
            .filter(
                Venda.id_produto.in_(ids),
                Venda.data_venda >= inicio,
                Venda.data_venda <= agora,
            )
            .group_by(Venda.id_produto)
            .all()
        )
        ultimos_ids = (
            db.session.query(
                PrecoConcorrente.id_produto,
                func.max(PrecoConcorrente.id_preco_concorrente).label("ultimo_id"),
            )
            .filter(PrecoConcorrente.id_produto.in_(ids))
            .group_by(PrecoConcorrente.id_produto)
            .subquery()
        )
        precos = {
            registro.id_produto: Decimal(str(registro.valor))
            for registro in db.session.query(PrecoConcorrente).join(
                ultimos_ids,
                PrecoConcorrente.id_preco_concorrente == ultimos_ids.c.ultimo_id,
            )
        }
        sugestoes = [
            self._montar_sugestao(
                produto,
                Decimal(str(giros.get(produto.id_produto) or 0)),
                precos.get(produto.id_produto),
                solicitante_id,
                persistir=False,
                configuracao=configuracao,
            )
            for produto in produtos
        ]
        db.session.add_all(sugestoes)
        db.session.commit()
        return sugestoes

    def _montar_sugestao(
            self,
            produto,
            giro,
            preco_concorrente,
            solicitante_id,
            feedback_cliente=None,
            persistir=False,
            configuracao=None,
    ):
        configuracao = configuracao or self.obter_configuracao()
        limiar_giro = Decimal(str(configuracao.limiar_giro))
        margem_minima = Decimal(str(configuracao.margem_minima))
        motivos = []
        preco = Decimal(str(produto.preco_atual))

        if giro < limiar_giro:
            preco *= Decimal("0.95")
            motivos.append("giro abaixo do limiar configurado")
        elif (
                limiar_giro > 0
                and giro >= limiar_giro * 2
                and preco_concorrente
                and preco < preco_concorrente
        ):
            preco *= Decimal("1.02")
            motivos.append("giro alto nos últimos 30 dias e preço abaixo do concorrente")
        hoje = datetime.utcnow().date()
        limite_validade = hoje + timedelta(days=configuracao.dias_validade)
        if produto.data_validade and hoje <= produto.data_validade < limite_validade:
            preco *= Decimal("0.90")
            motivos.append("validade próxima")
        if preco_concorrente and preco > preco_concorrente:
            preco = min(preco, preco_concorrente)
            motivos.append("preço acima do concorrente")
        if feedback_cliente:
            motivos.append("feedback de cliente")
        if not motivos:
            motivos.append("revisão preventiva de preço")

        preco = max(preco, Decimal(str(produto.custo)) * (1 + margem_minima / 100))
        preco = preco.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sugestao = SugestaoPreco(
            id_produto=produto.id_produto,
            id_solicitante=solicitante_id,
            preco_atual=produto.preco_atual,
            preco_sugerido=preco,
            giro_30_dias=giro,
            preco_concorrente=preco_concorrente,
            motivo="; ".join(motivos),
            feedback_cliente=feedback_cliente,
        )
        if persistir:
            return self.sugestoes.adicionar(sugestao)
        return sugestao

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
        if not isinstance(decisao, str):
            raise ValueError("Informe uma decisão válida.")
        decisao = decisao.upper()
        if decisao not in {"APROVADA", "EDITADA", "REJEITADA"}:
            raise ValueError("decisao deve ser APROVADA, EDITADA ou REJEITADA.")
        if decisao == "EDITADA":
            try:
                preco = Decimal(str(preco))
            except (ArithmeticError, TypeError, ValueError):
                raise ValueError("Informe um preço válido para uma sugestão editada.") from None
            if not preco.is_finite() or preco <= 0:
                raise ValueError("Informe um preço válido para uma sugestão editada.")
            sugestao.preco_sugerido = Decimal(str(preco))
        if decisao in {"APROVADA", "EDITADA"}:
            produto = self.produtos.buscar_por_id(sugestao.id_produto)
            if not produto:
                raise ValueError("O produto da sugestão não está mais ativo.")
            piso = Decimal(str(produto.custo)) * (
                    1 + Decimal(str(self.obter_configuracao().margem_minima)) / 100
            )
            if sugestao.preco_sugerido < piso:
                raise ValueError(
                    "O preço aprovado não pode ficar abaixo da margem mínima configurada."
                )
            preco_antigo = produto.preco_atual
            produto.preco_atual = sugestao.preco_sugerido
            db.session.add(
                HistoricoPreco(
                    id_produto=produto.id_produto,
                    usuario_id=aprovador_id,
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
