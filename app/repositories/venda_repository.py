from datetime import datetime, timedelta

from app.models.venda import Venda
from app.repositories.base_repository import BaseRepository


class VendaRepository(BaseRepository[Venda]):
    def __init__(self):
        super().__init__(Venda)

    def total_vendido(self, id_produto: int, dias: int = 30) -> float:
        inicio = datetime.utcnow() - timedelta(days=dias)
        vendas = Venda.query.filter(
            Venda.id_produto == id_produto,
            Venda.data_venda >= inicio,
        ).all()
        return sum(float(venda.quantidade) for venda in vendas)
