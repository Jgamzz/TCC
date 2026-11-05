from datetime import datetime

from app import db
from app.models.column_types import BIGINT_UNSIGNED


class FeedbackCliente(db.Model):
    __tablename__ = "feedback_cliente"

    id_feedback = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    id_produto = db.Column(
        BIGINT_UNSIGNED, db.ForeignKey("produto.id_produto"), nullable=False
    )
    cliente = db.Column(db.String(120), nullable=True)
    comentario = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processado = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            "id_feedback": self.id_feedback,
            "id_produto": self.id_produto,
            "cliente": self.cliente,
            "comentario": self.comentario,
            "data_criacao": self.data_criacao.isoformat(),
            "processado": self.processado,
        }
