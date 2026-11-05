from app.models.estoque import Estoque
from app.repositories.base_repository import BaseRepository


class EstoqueRepository(BaseRepository[Estoque]):
    def __init__(self):
        super().__init__(Estoque)

    def listar(self, limit=100, offset=0):
        return (
            self.model.query
            .order_by(self.model.data_operacao.desc(), self.model.id_estoque.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
