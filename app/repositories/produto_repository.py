from app.models.produto import Produto
from app.repositories.base_repository import BaseRepository
from sqlalchemy import or_


class ProdutoRepository(BaseRepository[Produto]):
    def __init__(self):
        super().__init__(Produto)

    def listar(self, filtros=None):
        filtros = filtros or {}
        consulta = Produto.query.filter_by(ativo=True)
        for campo in ("nome", "codigo", "categoria", "fornecedor"):
            valor = filtros.get(campo)
            if valor:
                consulta = consulta.filter(getattr(Produto, campo).ilike(f"%{valor.strip()}%"))
        disponivel = filtros.get("disponivel")
        if disponivel == "true":
            consulta = consulta.filter(Produto.estoque > 0)
        elif disponivel == "false":
            consulta = consulta.filter(Produto.estoque <= 0)
        return consulta.order_by(Produto.nome).all()

    def buscar_por_id(self, entity_id):
        produto = super().buscar_por_id(entity_id)
        return produto if produto and produto.ativo else None

    def buscar_com_bloqueio(self, entity_id):
        return (
            Produto.query.filter_by(id_produto=entity_id, ativo=True)
            .with_for_update()
            .first()
        )
