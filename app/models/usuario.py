from datetime import datetime

from app import db


class Usuario(db.Model):
    __tablename__ = "Usuario"

    id = db.Column("ID", db.Integer, primary_key=True, autoincrement=True)
    username = db.Column("Username", db.String(50), nullable=False, unique=True)
    password = db.Column("Password", db.String(255), nullable=False)
    email = db.Column("Email", db.String(254), nullable=True, unique=True)
    name = db.Column("Name", db.String(100), nullable=False)
    creation_date = db.Column("Creation_Date", db.DateTime, default=datetime.utcnow)
    is_active = db.Column("Is_Active", db.Boolean, default=True)
    failed_login_attempts = db.Column(
        db.SmallInteger, nullable=False, default=0, server_default="0"
    )
    locked_until = db.Column(db.DateTime, nullable=True)
    password_reset_requested_at = db.Column(db.DateTime, nullable=True)
    cargo_id = db.Column(
        "Cargo_ID",
        db.Integer,
        db.ForeignKey("Cargo.ID", ondelete="SET NULL"),
        nullable=True,
    )

    def to_dict(self):
        return {
            "ID": self.id,
            "Username": self.username,
            "Email": self.email,
            "Name": self.name,
            "Creation_Date": (
                self.creation_date.isoformat() if self.creation_date else None
            ),
            "Is_Active": self.is_active,
            "Cargo_ID": self.cargo_id,
            "Cargo_Name": self.cargo.name if self.cargo else None,
        }
