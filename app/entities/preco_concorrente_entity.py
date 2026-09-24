from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.entities.base_entity import BaseEntity


@dataclass
class PrecoConcorrenteEntity(BaseEntity):
    id_produto: int = 0
    valor: Decimal = Decimal("0")
    data_registro: datetime | None = None
