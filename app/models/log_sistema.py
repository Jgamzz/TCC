from datetime import datetime

from app import db
from app.models.column_types import BIGINT_UNSIGNED


class LogSistema(db.Model):
    __tablename__ = "log_sistema"

    id_log = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    nivel = db.Column(db.String(20), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    modulo = db.Column(db.String(255), nullable=True)
    metodo = db.Column(db.String(10), nullable=True)
    rota = db.Column(db.String(255), nullable=True)
    usuario_id = db.Column(db.Integer, nullable=True)
    stack_trace = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_log": self.id_log,
            "nivel": self.nivel,
            "mensagem": self.mensagem,
            "modulo": self.modulo,
            "metodo": self.metodo,
            "rota": self.rota,
            "usuario_id": self.usuario_id,
            "stack_trace": self.stack_trace,
            "data_criacao": self.data_criacao.isoformat(),
        }
