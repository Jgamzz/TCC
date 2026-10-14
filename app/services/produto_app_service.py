from decimal import Decimal

from app import db
from app.dtos.produto_dto import ProdutoRequestDto
from app.models.estoque import Estoque
from app.models.historico_preco import HistoricoPreco
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
        db.session.add(produto)
        db.session.flush()
        if produto.estoque > 0:
            db.session.add(
                Estoque(
                    id_produto=produto.id_produto,
                    tipo_operacao="ENTRADA",
                    quantidade=produto.estoque,
                    motivo="Estoque inicial no cadastro do produto",
                )
            )
        self.repository.salvar()
        return produto

    def atualizar(self, id_produto, dados):
        produto = self.buscar(id_produto)
        if not produto:
            return None
        dados = dados or {}
        estoque_anterior = Decimal(str(produto.estoque))
        preco_anterior = Decimal(str(produto.preco_atual))
        if "nome" in dados:
            produto.nome = dados["nome"].strip()
        for campo in ("custo", "preco_atual", "estoque"):
            if campo in dados:
                setattr(produto, campo, Decimal(str(dados[campo])))
        if produto.estoque < 0:
            raise ValueError("O estoque não pode ser negativo.")
        if produto.estoque != estoque_anterior:
            diferenca_estoque = produto.estoque - estoque_anterior
            db.session.add(
                Estoque(
                    id_produto=produto.id_produto,
                    tipo_operacao=(
                        "ENTRADA" if diferenca_estoque > 0 else "SAIDA"
                    ),
                    quantidade=abs(diferenca_estoque),
                    motivo="Ajuste de estoque pelo cadastro do produto",
                )
            )
        if produto.preco_atual != preco_anterior:
            db.session.add(
                HistoricoPreco(
                    id_produto=produto.id_produto,
                    preco_antigo=preco_anterior,
                    preco_novo=produto.preco_atual,
                    motivo="Atualização do cadastro do produto",
                )
            )
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
