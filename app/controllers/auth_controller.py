from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from app.dtos.auth_dto import LoginRequestDto, TokenResponseDto
from app.services.usuario_service import UsuarioService


class AuthController:
    """Endpoints públicos relacionados à autenticação."""

    blueprint = Blueprint("auth_bp", __name__)

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

        usuario, erro_credencial = UsuarioService.autenticar(
            login_dto.username, login_dto.password
        )
        if not usuario:
            if erro_credencial == "senha":
                return (
                    jsonify(
                        {
                            "erro": "Senha incorreta.",
                            "campos": ["senha"],
                        }
                    ),
                    401,
                )
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


auth_bp = AuthController.blueprint
