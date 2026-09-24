from decimal import Decimal

from app.dtos.produto_dto import ProdutoRequestDto
from app.models.produto import Produto
from app.repositories.produto_repository import ProdutoRepository


class ProdutoAppService:
    def __init__(self, repository=None):
        self.repository = repository or ProdutoRepository()

    def listar(self):
        return self.repository.listar()

    def buscar(self, id_produto):
        return self.repository.buscar_por_id(id_produto)

    def criar(self, dados):
        produto_dto = ProdutoRequestDto.from_dict(dados)
        produto = Produto(
            nome=produto_dto.nome,
            custo=produto_dto.custo,
            preco_atual=produto_dto.preco_atual,
            estoque=produto_dto.estoque,
            data_validade=produto_dto.data_validade,
        )
        return self.repository.adicionar(produto)

    def atualizar(self, id_produto, dados):
        produto = self.buscar(id_produto)
        if not produto:
            return None
        dados = dados or {}
        if "nome" in dados:
            produto.nome = dados["nome"].strip()
        for campo in ("custo", "preco_atual", "estoque"):
            if campo in dados:
                setattr(produto, campo, Decimal(str(dados[campo])))
        if "data_validade" in dados:
            produto.data_validade = ProdutoRequestDto._parse_date(
                dados["data_validade"]
            )
        self.repository.salvar()
        return produto

    def excluir(self, id_produto):
        produto = self.buscar(id_produto)
        if not produto:
            return False
        self.repository.excluir(produto)
        return True
