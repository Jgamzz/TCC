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
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    fornecedor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ProdutoRequestDto":
        if not isinstance(data, dict):
            raise ValueError("Os dados do produto devem ser um objeto JSON.")
        campos = ("nome", "custo", "preco_atual")
        ausentes = [campo for campo in campos if campo not in data]
        if ausentes:
            raise ValueError("Campos obrigatórios ausentes: " + ", ".join(ausentes))
        try:
            produto = cls(
                nome=str(data["nome"]).strip(),
                custo=Decimal(str(data["custo"])),
                preco_atual=Decimal(str(data["preco_atual"])),
                estoque=Decimal(str(data.get("estoque", 0))),
                data_validade=cls._parse_date(data.get("data_validade")),
                codigo=(cls._optional_text(data.get("codigo")) or "").upper() or None,
                descricao=cls._optional_text(data.get("descricao")),
                categoria=cls._optional_text(data.get("categoria")),
                fornecedor=cls._optional_text(data.get("fornecedor")),
            )
        except (ArithmeticError, TypeError, ValueError) as error:
            raise ValueError("Os valores numéricos do produto são inválidos.") from error
        if not produto.nome:
            raise ValueError("O nome do produto é obrigatório.")
        if len(produto.nome) > 150:
            raise ValueError("O nome do produto deve ter até 150 caracteres.")
        if produto.codigo and len(produto.codigo) > 80:
            raise ValueError("O código deve ter até 80 caracteres.")
        if produto.categoria and len(produto.categoria) > 100:
            raise ValueError("A categoria deve ter até 100 caracteres.")
        if produto.fornecedor and len(produto.fornecedor) > 150:
            raise ValueError("O fornecedor deve ter até 150 caracteres.")
        if (
            not produto.custo.is_finite()
            or not produto.preco_atual.is_finite()
            or not produto.estoque.is_finite()
            or produto.custo < 0
            or produto.preco_atual <= 0
            or produto.estoque < 0
        ):
            raise ValueError("Custo e estoque não podem ser negativos; preço deve ser positivo.")
        return produto

    @staticmethod
    def _optional_text(value):
        return str(value).strip() or None if value is not None else None

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
    codigo: Optional[str]
    descricao: Optional[str]
    categoria: Optional[str]
    fornecedor: Optional[str]
    ativo: bool

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
            codigo=produto.codigo,
            descricao=produto.descricao,
            categoria=produto.categoria,
            fornecedor=produto.fornecedor,
            ativo=produto.ativo,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_produto": self.id_produto,
            "nome": self.nome,
            "custo": self.custo,
            "preco_atual": self.preco_atual,
            "estoque": self.estoque,
            "data_validade": self.data_validade,
            "codigo": self.codigo,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "fornecedor": self.fornecedor,
            "ativo": self.ativo,
        }
