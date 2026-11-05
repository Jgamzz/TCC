from datetime import datetime, timedelta

from sqlalchemy import case, func

from app import db
from app.models.venda import Venda
from app.repositories.base_repository import BaseRepository


class VendaRepository(BaseRepository[Venda]):
    def __init__(self):
        super().__init__(Venda)

    def total_vendido(self, id_produto: int, dias: int = 30) -> float:
        agora = datetime.utcnow()
        inicio = agora - timedelta(days=dias)
        total = (
            db.session.query(func.coalesce(func.sum(Venda.quantidade), 0))
            .filter(
                Venda.id_produto == id_produto,
                Venda.data_venda >= inicio,
                Venda.data_venda <= agora,
            )
            .scalar()
        )
        return float(total)

    def totais_por_produto(
            self, id_produtos: list[int], agora: datetime | None = None
    ) -> dict[int, tuple[float, float]]:
        if not id_produtos:
            return {}

        agora = agora or datetime.utcnow()
        inicio_semanal = agora - timedelta(days=7)
        inicio_mensal = agora - timedelta(days=30)
        semana = func.coalesce(
            func.sum(
                case(
                    (Venda.data_venda >= inicio_semanal, Venda.quantidade),
                    else_=0,
                )
            ),
            0,
        )
        mes = func.coalesce(func.sum(Venda.quantidade), 0)
        resultados = (
            db.session.query(Venda.id_produto, semana, mes)
            .filter(
                Venda.id_produto.in_(id_produtos),
                Venda.data_venda >= inicio_mensal,
                Venda.data_venda <= agora,
            )
            .group_by(Venda.id_produto)
            .all()
        )
        return {
            id_produto: (float(total_semanal), float(total_mensal))
            for id_produto, total_semanal, total_mensal in resultados
        }
