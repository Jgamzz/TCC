from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.entities.base_entity import BaseEntity


@dataclass
class FeedbackClienteEntity(BaseEntity):
    id_produto: int = 0
    comentario: str = ""
    cliente: Optional[str] = None
    data_criacao: Optional[datetime] = None
    processado: bool = False
