from app import db
from app.models.produto import Produto


class ProdutoService:
    @staticmethod
    def listar_todos():
        return Produto.query.all()

    @staticmethod
    def buscar_por_id(id_produto):
        return Produto.query.get(id_produto)

    @staticmethod
    def criar_produto(dados):
        novo_produto = Produto(
            nome=dados["nome"],
            custo=dados["custo"],
            preco_atual=dados["preco_atual"],
            estoque=dados.get("estoque", 0),
            data_validade=dados.get("data_validade"),
        )
        db.session.add(novo_produto)
        db.session.commit()
        return novo_produto

    @staticmethod
    def atualizar_produto(id_produto, dados):
        produto = Produto.query.get(id_produto)
        if not produto:
            return None

        # Atualiza os campos se eles forem informados no JSON
        produto.nome = dados.get("nome", produto.nome)
        produto.custo = dados.get("custo", produto.custo)
        produto.preco_atual = dados.get("preco_atual", produto.preco_atual)
        produto.estoque = dados.get("estoque", produto.estoque)
        produto.data_validade = dados.get("data_validade", produto.data_validade)

        db.session.commit()
        return produto

    @staticmethod
    def deletar_produto(id_produto):
        produto = Produto.query.get(id_produto)
        if not produto:
            return False

        db.session.delete(produto)
        db.session.commit()
        return True
