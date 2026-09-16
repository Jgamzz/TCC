from app import db
from datetime import datetime
from app.models.column_types import BIGINT_UNSIGNED


class Produto(db.Model):
    __tablename__ = "produto"

    id_produto = db.Column(BIGINT_UNSIGNED, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(150), nullable=False, index=True)
    custo = db.Column(db.Numeric(12, 2), nullable=False)
    preco_atual = db.Column(db.Numeric(12, 2), nullable=False)
    estoque = db.Column(db.Numeric(12, 3), nullable=False, default=0.000)
    data_validade = db.Column(db.Date, nullable=True)

    # Relacionamentos
    vendas = db.relationship("Venda", backref="produto", lazy=True)
    precos_concorrentes = db.relationship(
        "PrecoConcorrente", backref="produto", lazy=True
    )
    historico_precos = db.relationship("HistoricoPreco", backref="produto", lazy=True)

    def to_dict(self):
        return {
            "id_produto": self.id_produto,
            "nome": self.nome,
            "custo": float(self.custo),
            "preco_atual": float(self.preco_atual),
            "estoque": float(self.estoque),
            "data_validade": (
                self.data_validade.isoformat() if self.data_validade else None
            ),
        }
