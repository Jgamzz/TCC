from app import db
from app.models.cargo import Cargo


class CargoService:
    @staticmethod
    def listar_todos():
        return Cargo.query.all()

    @staticmethod
    def buscar_por_id(id_cargo):
        return Cargo.query.get(id_cargo)

    @staticmethod
    def criar_cargo(dados):
        novo_cargo = Cargo(
            name=dados["Name"],
            is_active=dados.get("Is_Active", True),
        )
        db.session.add(novo_cargo)
        db.session.commit()
        return novo_cargo

    @staticmethod
    def atualizar_cargo(id_cargo, dados):
        cargo = Cargo.query.get(id_cargo)
        if not cargo:
            return None

        cargo.name = dados.get("Name", cargo.name)
        cargo.is_active = dados.get("Is_Active", cargo.is_active)

        db.session.commit()
        return cargo

    @staticmethod
    def deletar_cargo(id_cargo):
        cargo = Cargo.query.get(id_cargo)
        if not cargo:
            return False

        db.session.delete(cargo)
        db.session.commit()
        return True
