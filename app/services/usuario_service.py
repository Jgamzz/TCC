from functools import wraps
from datetime import datetime, timedelta
import re

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.usuario import Usuario
from app.services.auditoria_service import registrar_auditoria

ROLE_IDS = {"ADMIN": 1, "GERENTE": 2, "USUARIO": 3}
MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=15)


class UsuarioService:
    @staticmethod
    def listar_todos():
        return Usuario.query.all()

    @staticmethod
    def buscar_por_id(id_usuario):
        return db.session.get(Usuario, id_usuario)

    @staticmethod
    def criar_usuario(dados, ator_id=None):
        dados = dados or {}
        campos_obrigatorios = ("Username", "Password", "Name")
        ausentes = [campo for campo in campos_obrigatorios if not dados.get(campo)]
        if ausentes:
            raise ValueError("Campos obrigatórios ausentes: " + ", ".join(ausentes))
        if Usuario.query.filter_by(username=dados["Username"]).first():
            raise ValueError("Username já está em uso.")
        password = dados["Password"]
        if len(password) < 8:
            raise ValueError("A senha deve conter pelo menos 8 caracteres.")
        email = (dados.get("Email") or "").strip().lower() or None
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Informe um e-mail válido.")
        if email and Usuario.query.filter_by(email=email).first():
            raise ValueError("E-mail já está em uso.")

        usuario = Usuario(
            username=dados["Username"],
            password=generate_password_hash(password, method="scrypt"),
            email=email,
            name=dados["Name"],
            is_active=dados.get("Is_Active", True),
            cargo_id=dados.get("Cargo_ID"),
        )
        db.session.add(usuario)
        db.session.flush()
        registrar_auditoria(
            "USUARIO_CRIADO", "Usuario", usuario_id=ator_id, entidade_id=usuario.id,
            detalhes={"username": usuario.username, "cargo_id": usuario.cargo_id},
        )
        db.session.commit()
        return usuario

    @staticmethod
    def atualizar_usuario(id_usuario, dados, ator_id=None):
        usuario = UsuarioService.buscar_por_id(id_usuario)
        if not usuario:
            return None

        username = dados.get("Username")
        if username and username != usuario.username:
            existente = Usuario.query.filter_by(username=username).first()
            if existente:
                raise ValueError("Username já está em uso.")
            usuario.username = username
        if "Email" in dados:
            email = (dados.get("Email") or "").strip().lower() or None
            if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                raise ValueError("Informe um e-mail válido.")
            existente = Usuario.query.filter(
                Usuario.email == email, Usuario.id != id_usuario
            ).first() if email else None
            if existente:
                raise ValueError("E-mail já está em uso.")
            usuario.email = email

        campos = {
            "Name": "name",
            "Is_Active": "is_active",
            "Cargo_ID": "cargo_id",
        }
        for campo_json, campo_modelo in campos.items():
            if campo_json in dados:
                setattr(usuario, campo_modelo, dados[campo_json])
        if dados.get("Password"):
            if len(dados["Password"]) < 8:
                raise ValueError("A senha deve conter pelo menos 8 caracteres.")
            usuario.password = generate_password_hash(dados["Password"], method="scrypt")

        registrar_auditoria(
            "USUARIO_ATUALIZADO",
            "Usuario",
            usuario_id=ator_id,
            entidade_id=usuario.id,
            detalhes={"username": usuario.username},
        )
        db.session.commit()
        return usuario

    @staticmethod
    def autenticar(username, password):
        if not username or not password:
            return None, "usuario"

        usuario = Usuario.query.filter_by(username=username).first()
        if not usuario or not usuario.is_active:
            registrar_auditoria(
                "LOGIN_FALHO", "Usuario", detalhes={"username": username}
            )
            db.session.commit()
            return None, "credenciais"

        agora = datetime.utcnow()
        if usuario.locked_until and usuario.locked_until > agora:
            registrar_auditoria(
                "LOGIN_BLOQUEADO",
                "Usuario",
                usuario_id=usuario.id,
                entidade_id=usuario.id,
            )
            db.session.commit()
            return None, "credenciais"
        if usuario.locked_until and usuario.locked_until <= agora:
            usuario.locked_until = None
            usuario.failed_login_attempts = 0

        try:
            senha_valida = check_password_hash(usuario.password, password)
        except (ValueError, TypeError):
            senha_valida = False
        if not senha_valida:
            usuario.failed_login_attempts += 1
            if usuario.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                usuario.locked_until = agora + LOCK_DURATION
            registrar_auditoria(
                "LOGIN_FALHO",
                "Usuario",
                usuario_id=usuario.id,
                entidade_id=usuario.id,
            )
            db.session.commit()
            return None, "credenciais"

        usuario.failed_login_attempts = 0
        usuario.locked_until = None
        registrar_auditoria(
            "LOGIN_SUCESSO",
            "Usuario",
            usuario_id=usuario.id,
            entidade_id=usuario.id,
        )
        db.session.commit()
        return usuario, None

    @staticmethod
    def redefinir_senha(email, nova_senha):
        if len(nova_senha) < 8:
            raise ValueError("A senha deve conter pelo menos 8 caracteres.")
        usuario = Usuario.query.filter_by(email=email.strip().lower()).first()
        if not usuario:
            return False
        usuario.password = generate_password_hash(nova_senha, method="scrypt")
        usuario.failed_login_attempts = 0
        usuario.locked_until = None
        registrar_auditoria(
            "SENHA_REDEFINIDA",
            "Usuario",
            usuario_id=usuario.id,
            entidade_id=usuario.id,
        )
        db.session.commit()
        return True

    @staticmethod
    def deletar_usuario(id_usuario, ator_id=None):
        usuario = UsuarioService.buscar_por_id(id_usuario)
        if not usuario:
            return False
        usuario.is_active = False
        registrar_auditoria(
            "USUARIO_DESATIVADO",
            "Usuario",
            usuario_id=ator_id,
            entidade_id=id_usuario,
            detalhes={"username": usuario.username},
        )
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
