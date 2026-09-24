from app import db
from datetime import datetime
from app.models.column_types import BIGINT_UNSIGNED


class HistoricoPreco(db.Model):
    __tablename__ = "historico_preco"

    id_historico = db.Column(
        BIGINT_UNSIGNED, primary_key=True, autoincrement=True
    )
    id_produto = db.Column(
        BIGINT_UNSIGNED, db.ForeignKey("produto.id_produto"), nullable=False
    )
    preco_antigo = db.Column(db.Numeric(12, 2), nullable=False)
    preco_novo = db.Column(db.Numeric(12, 2), nullable=False)
    data_alteracao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    motivo = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id_historico": self.id_historico,
            "id_produto": self.id_produto,
            "preco_antigo": float(self.preco_antigo),
            "preco_novo": float(self.preco_novo),
            "data_alteracao": self.data_alteracao.isoformat(),
            "motivo": self.motivo,
        }
