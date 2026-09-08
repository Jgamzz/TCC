from app import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = 'Usuario'

    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(50), nullable=False, unique=True)
    Password = db.Column(db.String(50), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Creation_Date = db.Column(db.DateTime, default=datetime.utcnow)
    Is_Active = db.Column(db.Boolean, default=True)
    Cargo_ID = db.Column(db.Integer, db.ForeignKey('Cargo.ID', ondelete='SET NULL'), nullable=True)

    def to_dict(self):
        return {
            'ID': self.ID,
            'Username': self.Username,
            'Name': self.Name,
            'Creation_Date': self.Creation_Date.isoformat() if self.Creation_Date else None,
            'Is_Active': self.Is_Active,
            'Cargo_ID': self.Cargo_ID,
            'Cargo_Name': self.cargo.Name if self.cargo else None
        }