from app import db
from datetime import datetime
from app.models.column_types import BIGINT_UNSIGNED


class Venda(db.Model):
    __tablename__ = "venda"

    id_venda = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    id_produto = db.Column(
        BIGINT_UNSIGNED, db.ForeignKey("produto.id_produto"), nullable=False
    )
    data_venda = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)

    def to_dict(self):
        return {
            "id_venda": self.id_venda,
            "id_produto": self.id_produto,
            "data_venda": self.data_venda.isoformat(),
            "quantidade": float(self.quantidade),
        }
