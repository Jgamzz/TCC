from app.models.estoque import Estoque
from app.repositories.base_repository import BaseRepository


class EstoqueRepository(BaseRepository[Estoque]):
    def __init__(self):
        super().__init__(Estoque)
