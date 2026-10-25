from decimal import Decimal

from app import db
from app.models.estoque import Estoque
from app.models.venda import Venda
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.produto_repository import ProdutoRepository
from app.services.auditoria_service import registrar_auditoria


class EstoqueAppService:
    def __init__(
        self,
        produto_repository=None,
        venda_repository=None,
        estoque_repository=None,
    ):
        self.produto_repository = produto_repository or ProdutoRepository()
        self.estoque_repository = estoque_repository or EstoqueRepository()

    def listar(self, limit=100, offset=0):
        return self.estoque_repository.listar(limit=limit, offset=offset)

    def buscar(self, id_estoque):
        return self.estoque_repository.buscar_por_id(id_estoque)

    @staticmethod
    def _validar_operacao(tipo_operacao, quantidade, motivo):
        if not isinstance(tipo_operacao, str):
            raise ValueError("tipo_operacao deve ser ENTRADA ou SAIDA.")
        tipo_operacao = tipo_operacao.strip().upper()
        if tipo_operacao not in {"ENTRADA", "SAIDA"}:
            raise ValueError("tipo_operacao deve ser ENTRADA ou SAIDA.")
        try:
            quantidade = Decimal(str(quantidade))
        except (ArithmeticError, ValueError):
            raise ValueError("A quantidade deve ser um número válido.") from None
        if not quantidade.is_finite() or quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError("O motivo da movimentação é obrigatório.")
        return tipo_operacao, quantidade, motivo.strip()

    @staticmethod
    def _impacto(tipo_operacao, quantidade):
        return quantidade if tipo_operacao == "ENTRADA" else -quantidade

    def criar(self, dados, usuario_id=None):
        dados = dados or {}
        if not isinstance(dados, dict):
            raise ValueError("Os dados da movimentação devem ser um objeto.")
        try:
            id_produto = int(dados["id_produto"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("id_produto é obrigatório e deve ser válido.") from None

        produto = self.produto_repository.buscar_com_bloqueio(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")
        if not produto.ativo:
            raise ValueError("Não é permitido movimentar um produto inativo.")
        tipo_operacao, quantidade, motivo = self._validar_operacao(
            dados.get("tipo_operacao"), dados.get("quantidade"), dados.get("motivo")
        )
        impacto = self._impacto(tipo_operacao, quantidade)
        if Decimal(str(produto.estoque)) + impacto < 0:
            raise ValueError("Estoque insuficiente para registrar a saída.")

        produto.estoque = Decimal(str(produto.estoque)) + impacto
        movimento = Estoque(
            id_produto=id_produto,
            tipo_operacao=tipo_operacao,
            quantidade=quantidade,
            motivo=motivo,
            usuario_id=usuario_id,
        )
        db.session.add(movimento)
        db.session.flush()
        registrar_auditoria(
            "ESTOQUE_MOVIMENTADO",
            "Estoque",
            usuario_id=usuario_id,
            entidade_id=movimento.id_estoque,
            detalhes={
                "id_produto": id_produto,
                "tipo_operacao": tipo_operacao,
                "quantidade": str(quantidade),
                "motivo": motivo,
            },
        )
        db.session.commit()
        return movimento

    def atualizar(self, id_estoque, dados):
        raise ValueError(
            "Movimentações são imutáveis; registre uma movimentação compensatória."
        )

    def excluir(self, id_estoque):
        raise ValueError("Movimentações são imutáveis e não podem ser removidas.")

    def registrar_venda(
        self, id_produto, quantidade, data_venda=None, usuario_id=None, motivo=None
    ):
        produto = self.produto_repository.buscar_com_bloqueio(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")
        if not produto.ativo:
            raise ValueError("Não é permitido vender um produto inativo.")
        try:
            quantidade = Decimal(str(quantidade))
        except (ArithmeticError, ValueError):
            raise ValueError("A quantidade da venda deve ser válida.") from None
        if not quantidade.is_finite() or quantidade <= 0:
            raise ValueError("A quantidade da venda deve ser maior que zero.")
        if quantidade > produto.estoque:
            raise ValueError("Estoque insuficiente para registrar a venda.")

        venda = Venda(
            id_produto=id_produto,
            quantidade=quantidade,
            data_venda=data_venda,
            preco_unitario=produto.preco_atual,
        )
        produto.estoque -= quantidade
        movimento = Estoque(
            id_produto=id_produto,
            tipo_operacao="VENDA",
            quantidade=quantidade,
            motivo=(motivo.strip() if isinstance(motivo, str) and motivo.strip() else "Venda registrada"),
            usuario_id=usuario_id,
        )
        db.session.add(movimento)
        registrar_auditoria(
            "VENDA_REGISTRADA",
            "Venda",
            usuario_id=usuario_id,
            detalhes={
                "id_produto": id_produto,
                "quantidade": str(quantidade),
                "motivo": movimento.motivo,
            },
        )
        db.session.add(venda)
        db.session.commit()
        return venda
