from app import db
from datetime import datetime

class Cargo(db.Model):
    __tablename__ = 'Cargo'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), nullable=False)
    Creation_Date = db.Column(db.DateTime, default=datetime.utcnow)
    Is_Active = db.Column(db.Boolean, default=True)

    # Relacionamento de 1 para N com Usuario
    usuarios = db.relationship('Usuario', backref='cargo', lazy=True)

    def to_dict(self):
        return {
            'ID': self.ID,
            'Name': self.Name,
            'Creation_Date': self.Creation_Date.isoformat() if self.Creation_Date else None,
            'Is_Active': self.Is_Active
        }