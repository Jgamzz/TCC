from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models.usuario import Usuario

ROLE_IDS = {"ADMIN": 1, "GERENTE": 2, "USUARIO": 3}


class UsuarioService:
    @staticmethod
    def listar_todos():
        return Usuario.query.all()

    @staticmethod
    def buscar_por_id(id_usuario):
        return db.session.get(Usuario, id_usuario)

    @staticmethod
    def criar_usuario(dados):
        dados = dados or {}
        campos_obrigatorios = ("Username", "Password", "Name")
        ausentes = [campo for campo in campos_obrigatorios if not dados.get(campo)]
        if ausentes:
            raise ValueError("Campos obrigatórios ausentes: " + ", ".join(ausentes))
        if Usuario.query.filter_by(username=dados["Username"]).first():
            raise ValueError("Username já está em uso.")

        usuario = Usuario(
            username=dados["Username"],
            password=dados["Password"],
            name=dados["Name"],
            is_active=dados.get("Is_Active", True),
            cargo_id=dados.get("Cargo_ID"),
        )
        db.session.add(usuario)
        db.session.commit()
        return usuario

    @staticmethod
    def atualizar_usuario(id_usuario, dados):
        usuario = UsuarioService.buscar_por_id(id_usuario)
        if not usuario:
            return None

        username = dados.get("Username")
        if username and username != usuario.username:
            existente = Usuario.query.filter_by(username=username).first()
            if existente:
                raise ValueError("Username já está em uso.")
            usuario.username = username

        campos = {
            "Name": "name",
            "Is_Active": "is_active",
            "Cargo_ID": "cargo_id",
        }
        for campo_json, campo_modelo in campos.items():
            if campo_json in dados:
                setattr(usuario, campo_modelo, dados[campo_json])
        if dados.get("Password"):
            usuario.password = dados["Password"]

        db.session.commit()
        return usuario

    @staticmethod
    def autenticar(username, password):
        if not username or not password:
            return None

        usuario = Usuario.query.filter_by(username=username).first()
        if not usuario or not usuario.is_active:
            return None

        return usuario if usuario.password == password else None

    @staticmethod
    def deletar_usuario(id_usuario):
        usuario = UsuarioService.buscar_por_id(id_usuario)
        if not usuario:
            return False
        db.session.delete(usuario)
        db.session.commit()
        return True


def verificar_permissao(cargos_permitidos):
    ids_permitidos = {
        ROLE_IDS.get(cargo.upper(), cargo) if isinstance(cargo, str) else cargo
        for cargo in cargos_permitidos
    }

    def decorator(funcao):
        @wraps(funcao)
        @jwt_required()
        def wrapper(*args, **kwargs):
            usuario = db.session.get(Usuario, int(get_jwt_identity()))
            if not usuario or not usuario.is_active:
                return jsonify({"erro": "Usuário inválido ou inativo."}), 403
            request.usuario = usuario
            if usuario.cargo_id not in ids_permitidos:
                return (
                    jsonify(
                        {
                            "erro": (
                                "Usuário não permitido para esta ação. "
                                "Verifique as permissões do seu cargo."
                            )
                        }
                    ),
                    403,
                )
            return funcao(*args, **kwargs)

        return wrapper

    return decorator
