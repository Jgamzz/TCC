from app.models.produto import Produto
from app.repositories.base_repository import BaseRepository


class ProdutoRepository(BaseRepository[Produto]):
    def __init__(self):
        super().__init__(Produto)
