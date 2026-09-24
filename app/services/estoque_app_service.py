from decimal import Decimal

from app.models.venda import Venda
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.venda_repository import VendaRepository


class EstoqueAppService:
    def __init__(self, produto_repository=None, venda_repository=None):
        self.produto_repository = produto_repository or ProdutoRepository()
        self.venda_repository = venda_repository or VendaRepository()

    def registrar_venda(self, id_produto, quantidade, data_venda=None):
        produto = self.produto_repository.buscar_por_id(id_produto)
        if not produto:
            raise ValueError("Produto não encontrado.")
        quantidade = Decimal(str(quantidade))
        if quantidade <= 0:
            raise ValueError("A quantidade da venda deve ser maior que zero.")
        if quantidade > produto.estoque:
            raise ValueError("Estoque insuficiente para registrar a venda.")

        venda = Venda(
            id_produto=id_produto,
            quantidade=quantidade,
            data_venda=data_venda,
        )
        produto.estoque -= quantidade
        return self.venda_repository.adicionar(venda)
