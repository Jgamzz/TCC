from typing import Generic, Optional, Type, TypeVar

from app import db

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Operações persistentes comuns às entidades SQLAlchemy."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def listar(self):
        return self.model.query.all()

    def buscar_por_id(self, entity_id) -> Optional[ModelType]:
        return db.session.get(self.model, entity_id)

    def adicionar(self, entity: ModelType) -> ModelType:
        db.session.add(entity)
        db.session.commit()
        return entity

    def salvar(self) -> None:
        db.session.commit()

    def excluir(self, entity: ModelType) -> None:
        db.session.delete(entity)
        db.session.commit()
