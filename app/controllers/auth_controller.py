import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.dtos.auth_dto import LoginRequestDto, TokenResponseDto
from app.services.usuario_service import UsuarioService


class AuthController:
    """Endpoints públicos relacionados à autenticação."""

    blueprint = Blueprint("auth_bp", __name__)

    @staticmethod
    def _serializer():
        return URLSafeTimedSerializer(
            current_app.config["JWT_SECRET_KEY"],
            salt=current_app.config["PASSWORD_RESET_SALT"],
        )

    @staticmethod
    @blueprint.post("/login")
    def login():
        """
        Autentica um usuário e retorna um JWT.
        ---
        tags:
          - Autenticação
        consumes:
          - application/json
        parameters:
          - in: body
            name: credenciais
            required: true
            schema:
              type: object
              required: [Username, Password]
              properties:
                Username:
                  type: string
                  example: admin
                Password:
                  type: string
                  format: password
                  example: senha123
        responses:
          200:
            description: Token JWT gerado
          401:
            description: Credenciais inválidas
        """
        try:
            login_dto = LoginRequestDto.from_dict(request.get_json(silent=True))
        except ValueError as error:
            return jsonify({"erro": str(error)}), 400

        usuario, _erro_credencial = UsuarioService.autenticar(
            login_dto.username, login_dto.password
        )
        if not usuario:
            return (
                jsonify(
                    {
                        "erro": "Usuário e senha incorretos.",
                        "campos": ["usuario", "senha"],
                    }
                ),
                401,
            )
        if usuario.cargo_id is None:
            return (
                jsonify({"erro": "Usuário autenticado, mas sem cargo definido."}),
                403,
            )

        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={"cargo_id": usuario.cargo_id},
        )
        return jsonify(
            TokenResponseDto(access_token=token, usuario=usuario.to_dict()).to_dict()
        )

    @staticmethod
    @blueprint.post("/recuperar-senha")
    def solicitar_recuperacao():
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"erro": "Informe um objeto JSON."}), 400
        email = str(dados.get("email", "")).strip().lower()
        if not email:
            return jsonify({"erro": "E-mail é obrigatório."}), 400
        resposta = {
            "mensagem": "Se o e-mail estiver cadastrado, enviaremos as instruções."
        }
        smtp_host = current_app.config.get("SMTP_HOST")
        remetente = current_app.config.get("SMTP_FROM")
        if not smtp_host or not remetente:
            current_app.logger.error("Recuperação de senha sem SMTP configurado.")
            return jsonify({"erro": "Serviço de recuperação indisponível."}), 503
        from app import db
        from app.models.usuario import Usuario

        usuario = Usuario.query.filter_by(email=email, is_active=True).first()
        if not usuario:
            return jsonify(resposta), 202
        agora = datetime.utcnow()
        if (
            usuario.password_reset_requested_at
            and usuario.password_reset_requested_at > agora - timedelta(minutes=1)
        ):
            return jsonify(resposta), 202
        token = AuthController._serializer().dumps(email)
        link = f"{current_app.config['APP_PUBLIC_URL'].rstrip('/')}/?reset_token={token}"
        mensagem = EmailMessage()
        mensagem["Subject"] = "Redefinição de senha do SGB Varejo"
        mensagem["From"] = remetente
        mensagem["To"] = email
        mensagem.set_content(
            "Foi solicitada a redefinição da senha. "
            f"Acesse este link em até 15 minutos: {link}"
        )
        with smtplib.SMTP(
            smtp_host, current_app.config["SMTP_PORT"], timeout=10
        ) as servidor:
            servidor.starttls()
            username = current_app.config.get("SMTP_USERNAME")
            password = current_app.config.get("SMTP_PASSWORD")
            if username and password:
                servidor.login(username, password)
            servidor.send_message(mensagem)
        usuario.password_reset_requested_at = agora
        db.session.commit()
        return jsonify(resposta), 202

    @staticmethod
    @blueprint.post("/redefinir-senha")
    def redefinir_senha():
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"erro": "Informe um objeto JSON."}), 400
        token = dados.get("token")
        nova_senha = dados.get("nova_senha")
        if not isinstance(token, str) or not isinstance(nova_senha, str):
            return jsonify({"erro": "Token e nova senha são obrigatórios."}), 400
        try:
            email = AuthController._serializer().loads(
                token,
                max_age=current_app.config["PASSWORD_RESET_MAX_AGE_SECONDS"],
            )
        except (BadSignature, SignatureExpired):
            return jsonify({"erro": "O link expirou ou é inválido."}), 400
        try:
            UsuarioService.redefinir_senha(email, nova_senha)
        except ValueError as erro:
            return jsonify({"erro": str(erro)}), 400
        return jsonify({"mensagem": "Senha redefinida com sucesso."})


auth_bp = AuthController.blueprint
