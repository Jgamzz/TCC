from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ProdutoRequestDto:
    nome: str
    custo: Decimal
    preco_atual: Decimal
    estoque: Decimal = Decimal("0")
    data_validade: Optional[date] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ProdutoRequestDto":
        data = data or {}
        campos = ("nome", "custo", "preco_atual")
        ausentes = [campo for campo in campos if campo not in data]
        if ausentes:
            raise ValueError("Campos obrigatórios ausentes: " + ", ".join(ausentes))
        return cls(
            nome=str(data["nome"]).strip(),
            custo=Decimal(str(data["custo"])),
            preco_atual=Decimal(str(data["preco_atual"])),
            estoque=Decimal(str(data.get("estoque", 0))),
            data_validade=cls._parse_date(data.get("data_validade")),
        )

    @staticmethod
    def _parse_date(value: Any) -> Optional[date]:
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "data_validade deve estar no formato AAAA-MM-DD."
            ) from error


@dataclass(frozen=True)
class ProdutoResponseDto:
    id_produto: int
    nome: str
    custo: float
    preco_atual: float
    estoque: float
    data_validade: Optional[str]

    @classmethod
    def from_model(cls, produto) -> "ProdutoResponseDto":
        return cls(
            id_produto=produto.id_produto,
            nome=produto.nome,
            custo=float(produto.custo),
            preco_atual=float(produto.preco_atual),
            estoque=float(produto.estoque),
            data_validade=(
                produto.data_validade.isoformat() if produto.data_validade else None
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_produto": self.id_produto,
            "nome": self.nome,
            "custo": self.custo,
            "preco_atual": self.preco_atual,
            "estoque": self.estoque,
            "data_validade": self.data_validade,
        }
