from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.entities.base_entity import BaseEntity


@dataclass
class VendaEntity(BaseEntity):
    id_produto: int = 0
    quantidade: Decimal = Decimal("0")
    data_venda: datetime | None = None
