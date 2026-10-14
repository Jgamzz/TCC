from datetime import datetime

from app import db
from app.models.column_types import BIGINT_UNSIGNED


class Estoque(db.Model):
    __tablename__ = "Estoque"

    id_estoque = db.Column(
        "ID_Estoque", BIGINT_UNSIGNED, primary_key=True, autoincrement=True
    )
    id_produto = db.Column(
        BIGINT_UNSIGNED, db.ForeignKey("produto.id_produto"), nullable=False
    )
    tipo_operacao = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    data_operacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    produto = db.relationship(
        "Produto", backref=db.backref("movimentacoes_estoque", lazy=True)
    )

    def to_dict(self):
        return {
            "id_estoque": self.id_estoque,
            "id_produto": self.id_produto,
            "tipo_operacao": self.tipo_operacao,
            "quantidade": float(self.quantidade),
            "motivo": self.motivo,
            "data_operacao": self.data_operacao.isoformat(),
        }
