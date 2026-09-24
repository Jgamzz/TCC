from app.models.sugestao_preco import SugestaoPreco
from app.repositories.base_repository import BaseRepository


class SugestaoPrecoRepository(BaseRepository[SugestaoPreco]):
    def __init__(self):
        super().__init__(SugestaoPreco)

    def pendentes(self):
        return (
            SugestaoPreco.query.filter_by(status="PENDENTE")
            .order_by(SugestaoPreco.data_criacao.desc())
            .all()
        )
