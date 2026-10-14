from datetime import datetime
from decimal import Decimal

from app import db
from app.models.estoque import Estoque
from app.models.venda import Venda
from app.repositories.estoque_repository import EstoqueRepository
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.venda_repository import VendaRepository


class EstoqueAppService:
    def __init__(
        self,
        produto_repository=None,
        venda_repository=None,
        estoque_repository=None,
    ):
        self.produto_repository = produto_repository or ProdutoRepository()
        self.venda_repository = venda_repository or VendaRepository()
        self.estoque_repository = estoque_repository or EstoqueRepository()

    def listar(self):
        return self.estoque_repository.listar()

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

    def criar(self, dados):
        dados = dados or {}
        if not isinstance(dados, dict):
            raise ValueError("Os dados da movimentação devem ser um objeto.")
        try:
            id_produto = int(dados["id_produto"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("id_produto é obrigatório e deve ser válido.") from None

        produto = self.produto_repository.buscar_por_id(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")
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
        )
        return self.estoque_repository.adicionar(movimento)

    def atualizar(self, id_estoque, dados):
        movimento = self.buscar(id_estoque)
        if not movimento:
            return None
        dados = dados or {}
        if not isinstance(dados, dict):
            raise ValueError("Os dados da movimentação devem ser um objeto.")

        try:
            id_produto = int(dados.get("id_produto", movimento.id_produto))
        except (TypeError, ValueError):
            raise ValueError("id_produto deve ser válido.") from None
        produto_anterior = self.produto_repository.buscar_por_id(
            movimento.id_produto
        )
        produto_novo = self.produto_repository.buscar_por_id(id_produto)
        if not produto_novo:
            raise ValueError("Produto não encontrado.")

        tipo_operacao, quantidade, motivo = self._validar_operacao(
            dados.get("tipo_operacao", movimento.tipo_operacao),
            dados.get("quantidade", movimento.quantidade),
            dados.get("motivo", movimento.motivo),
        )
        impacto_anterior = self._impacto(
            movimento.tipo_operacao, Decimal(str(movimento.quantidade))
        )
        impacto_novo = self._impacto(tipo_operacao, quantidade)

        if produto_anterior.id_produto == produto_novo.id_produto:
            estoque_resultante = (
                Decimal(str(produto_anterior.estoque))
                - impacto_anterior
                + impacto_novo
            )
            if estoque_resultante < 0:
                raise ValueError("A alteração deixaria o estoque negativo.")
            produto_anterior.estoque = estoque_resultante
        else:
            estoque_anterior = (
                Decimal(str(produto_anterior.estoque)) - impacto_anterior
            )
            estoque_novo = Decimal(str(produto_novo.estoque)) + impacto_novo
            if estoque_anterior < 0 or estoque_novo < 0:
                raise ValueError("A alteração deixaria um estoque negativo.")
            produto_anterior.estoque = estoque_anterior
            produto_novo.estoque = estoque_novo

        movimento.id_produto = id_produto
        movimento.tipo_operacao = tipo_operacao
        movimento.quantidade = quantidade
        movimento.motivo = motivo
        movimento.data_operacao = datetime.utcnow()
        self.estoque_repository.salvar()
        return movimento

    def excluir(self, id_estoque):
        movimento = self.buscar(id_estoque)
        if not movimento:
            return False
        produto = self.produto_repository.buscar_por_id(movimento.id_produto)
        impacto = self._impacto(
            movimento.tipo_operacao, Decimal(str(movimento.quantidade))
        )
        estoque_resultante = Decimal(str(produto.estoque)) - impacto
        if estoque_resultante < 0:
            raise ValueError("A exclusão deixaria o estoque negativo.")
        produto.estoque = estoque_resultante
        self.estoque_repository.excluir(movimento)
        return True

    def registrar_venda(self, id_produto, quantidade, data_venda=None):
        produto = self.produto_repository.buscar_por_id(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")
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
        )
        produto.estoque -= quantidade
        db.session.add(
            Estoque(
                id_produto=id_produto,
                tipo_operacao="SAIDA",
                quantidade=quantidade,
                motivo="Venda registrada",
            )
        )
        return self.venda_repository.adicionar(venda)
