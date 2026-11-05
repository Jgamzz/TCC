from datetime import datetime

from app import db


class Cargo(db.Model):
    __tablename__ = "Cargo"

    id = db.Column("ID", db.Integer, primary_key=True, autoincrement=True)
    name = db.Column("Name", db.String(50), nullable=False)
    creation_date = db.Column("Creation_Date", db.DateTime, default=datetime.utcnow)
    is_active = db.Column("Is_Active", db.Boolean, default=True)

    # Relacionamento de 1 para N com Usuario
    usuarios = db.relationship("Usuario", backref="cargo", lazy=True)

    def to_dict(self):
        return {
            "ID": self.id,
            "Name": self.name,
            "Creation_Date": (
                self.creation_date.isoformat() if self.creation_date else None
            ),
            "Is_Active": self.is_active,
        }
