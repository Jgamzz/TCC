from datetime import datetime

from sqlalchemy import Index, UniqueConstraint

from app import db


class PrecoConcorrentePlanilha(db.Model):
    __tablename__ = "preco_concorrente_planilha"
    __table_args__ = (
        UniqueConstraint(
            "nome_arquivo",
            "nome_aba",
            "linha_excel",
            name="uq_preco_planilha_origem",
        ),
        Index("ix_preco_planilha_produto", "nome_produto"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_aba = db.Column(db.String(100), nullable=False)
    linha_excel = db.Column(db.Integer, nullable=False)
    nome_produto = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_importacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
