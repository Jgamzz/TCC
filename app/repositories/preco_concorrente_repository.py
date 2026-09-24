from sqlalchemy import desc

from app.models.preco_concorrente import PrecoConcorrente
from app.repositories.base_repository import BaseRepository


class PrecoConcorrenteRepository(BaseRepository[PrecoConcorrente]):
    def __init__(self):
        super().__init__(PrecoConcorrente)

    def ultimo_por_produto(self, id_produto: int):
        return (
            PrecoConcorrente.query.filter_by(id_produto=id_produto)
            .order_by(desc(PrecoConcorrente.data_registro))
            .first()
        )
