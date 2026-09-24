from app import db


class ConfiguracaoRegras(db.Model):
    __tablename__ = "configuracao_regras"

    id_configuracao = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    limiar_giro = db.Column(db.Numeric(12, 3), nullable=False)
    dias_validade = db.Column(db.SmallInteger, nullable=False)
    margem_minima = db.Column(db.Numeric(7, 3), nullable=False)

    def to_dict(self):
        return {
            "id_configuracao": self.id_configuracao,
            "limiar_giro": float(self.limiar_giro),
            "dias_validade": self.dias_validade,
            "margem_minima": float(self.margem_minima),
        }
