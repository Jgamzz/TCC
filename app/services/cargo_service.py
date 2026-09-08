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
            Name=dados['Name'],
            Is_Active=dados.get('Is_Active', True)
        )
        db.session.add(novo_cargo)
        db.session.commit()
        return novo_cargo

    @staticmethod
    def atualizar_cargo(id_cargo, dados):
        cargo = Cargo.query.get(id_cargo)
        if not cargo:
            return None

        cargo.Name = dados.get('Name', cargo.Name)
        cargo.Is_Active = dados.get('Is_Active', cargo.Is_Active)

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