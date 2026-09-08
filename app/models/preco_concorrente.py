from app import db
from datetime import datetime

class PrecoConcorrente(db.Model):
    __tablename__ = 'preco_concorrente'

    id_preco_concorrente = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_produto = db.Column(db.BigInteger, db.ForeignKey('produto.id_produto'), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id_preco_concorrente': self.id_preco_concorrente,
            'id_produto': self.id_produto,
            'valor': float(self.valor),
            'data_registro': self.data_registro.isoformat()
        }