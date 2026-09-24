from datetime import datetime

from app import db
from app.models.column_types import BIGINT_UNSIGNED


class SugestaoPreco(db.Model):
    __tablename__ = "sugestao_preco"

    id_sugestao = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    id_produto = db.Column(
        BIGINT_UNSIGNED, db.ForeignKey("produto.id_produto"), nullable=False
    )
    id_solicitante = db.Column(db.Integer, db.ForeignKey("Usuario.ID"), nullable=True)
    id_aprovador = db.Column(db.Integer, db.ForeignKey("Usuario.ID"), nullable=True)
    preco_atual = db.Column(db.Numeric(12, 2), nullable=False)
    preco_sugerido = db.Column(db.Numeric(12, 2), nullable=False)
    giro_30_dias = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    preco_concorrente = db.Column(db.Numeric(12, 2), nullable=True)
    motivo = db.Column(db.Text, nullable=False)
    origem = db.Column(db.String(30), nullable=False, default="MOTOR")
    feedback_cliente = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="PENDENTE")
    observacao_aprovacao = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_decisao = db.Column(db.DateTime, nullable=True)

    produto = db.relationship(
        "Produto", backref=db.backref("sugestoes_preco", lazy=True)
    )

    def to_dict(self):
        return {
            "id_sugestao": self.id_sugestao,
            "id_produto": self.id_produto,
            "id_solicitante": self.id_solicitante,
            "id_aprovador": self.id_aprovador,
            "preco_atual": float(self.preco_atual),
            "preco_sugerido": float(self.preco_sugerido),
            "giro_30_dias": float(self.giro_30_dias),
            "preco_concorrente": (
                float(self.preco_concorrente)
                if self.preco_concorrente is not None
                else None
            ),
            "motivo": self.motivo,
            "origem": self.origem,
            "feedback_cliente": self.feedback_cliente,
            "status": self.status,
            "observacao_aprovacao": self.observacao_aprovacao,
            "data_criacao": self.data_criacao.isoformat(),
            "data_decisao": (
                self.data_decisao.isoformat() if self.data_decisao else None
            ),
        }
