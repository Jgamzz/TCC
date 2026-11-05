from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.entities.base_entity import BaseEntity


@dataclass
class SugestaoPrecoEntity(BaseEntity):
    id_produto: int = 0
    preco_atual: Decimal = Decimal("0")
    preco_sugerido: Decimal = Decimal("0")
    motivo: str = ""
    status: str = "PENDENTE"
    id_solicitante: Optional[int] = None
    id_aprovador: Optional[int] = None
