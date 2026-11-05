from datetime import datetime

from app import db
from app.models.column_types import BIGINT_UNSIGNED


class Auditoria(db.Model):
    __tablename__ = "auditoria"

    id_auditoria = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("Usuario.ID"), nullable=True)
    acao = db.Column(db.String(80), nullable=False, index=True)
    entidade = db.Column(db.String(80), nullable=False)
    entidade_id = db.Column(db.String(80), nullable=True)
    detalhes = db.Column(db.JSON, nullable=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_auditoria": self.id_auditoria,
            "usuario_id": self.usuario_id,
            "acao": self.acao,
            "entidade": self.entidade,
            "entidade_id": self.entidade_id,
            "detalhes": self.detalhes,
            "data_criacao": self.data_criacao.isoformat(),
        }
