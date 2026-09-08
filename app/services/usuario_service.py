from functools import wraps
from flask import request, jsonify
from app import db
from app.models.usuario import Usuario


class UsuarioService:
    @staticmethod
    def listar_todos():
        return Usuario.query.all()

    @staticmethod
    def buscar_por_id(id_usuario):
        return Usuario.query.get(id_usuario)

    @staticmethod
    def criar_usuario(dados):
        if Usuario.query.filter_by(Username=dados['Username']).first():
            raise ValueError("Username já está em uso.")

        novo_usuario = Usuario(
            Username=dados['Username'],
            Password=dados['Password'],
            Name=dados['Name'],
            Is_Active=dados.get('Is_Active', True),
            Cargo_ID=dados.get('Cargo_ID')
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return novo_usuario

    @staticmethod
    def atualizar_usuario(id_usuario, dados):
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return None

        novo_username = dados.get('Username')
        if novo_username and novo_username != usuario.Username:
            if Usuario.query.filter_by(Username=novo_username).first():
                raise ValueError("Username já está em uso.")
            usuario.Username = novo_username

        usuario.Password = dados.get('Password', usuario.Password)
        usuario.Name = dados.get('Name', usuario.Name)
        usuario.Is_Active = dados.get('Is_Active', usuario.Is_Active)
        usuario.Cargo_ID = dados.get('Cargo_ID', usuario.Cargo_ID)

        db.session.commit()
        return usuario

    @staticmethod
    def deletar_usuario(id_usuario):
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return False

        db.session.delete(usuario)
        db.session.commit()
        return True


# Decorator de Permissões por Cargo (1: Funcionário, 2: Gerente, 3: Dono)
def verificar_permissao(cargos_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return jsonify({"erro": "Acesso não autorizado. Cabeçalho 'X-User-ID' ausente."}), 401

            usuario = Usuario.query.get(user_id)
            if not usuario or not usuario.Is_Active:
                return jsonify({"erro": "Usuário inválido ou inativo."}), 403

            if usuario.Cargo_ID not in cargos_permitidos:
                return jsonify({"erro": "Seu cargo não tem permissão para realizar esta ação."}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator