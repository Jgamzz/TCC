from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from app.entities.base_entity import BaseEntity


@dataclass
class ProdutoEntity(BaseEntity):
    nome: str = ""
    custo: Decimal = Decimal("0")
    preco_atual: Decimal = Decimal("0")
    estoque: Decimal = Decimal("0")
    data_validade: Optional[date] = None

    def possui_estoque(self, quantidade: Decimal) -> bool:
        return self.estoque >= quantidade

    def reduzir_estoque(self, quantidade: Decimal) -> None:
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        if not self.possui_estoque(quantidade):
            raise ValueError("Estoque insuficiente para a operação.")
        self.estoque -= quantidade
