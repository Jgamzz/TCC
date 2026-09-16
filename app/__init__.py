from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    from app.logging_config import configurar_logging, registrar_erro

    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    jwt.init_app(flask_app)

    @jwt.unauthorized_loader
    def handle_missing_token(_error):
        return {
            "erro": "Usuário não permitido. Faça login para acessar este recurso."
        }, 401

    @jwt.invalid_token_loader
    def handle_invalid_token(_error):
        return {"erro": "Usuário não permitido. O token informado é inválido."}, 401

    @jwt.expired_token_loader
    def handle_expired_token(_header, _payload):
        return {"erro": "Sua sessão expirou. Faça login novamente para continuar."}, 401

    @jwt.revoked_token_loader
    def handle_revoked_token(_header, _payload):
        return {"erro": "Usuário não permitido. Este token foi revogado."}, 401

    flask_app.config["SWAGGER"] = {
        "title": "SGB Varejo - API TCC",
        "uiversion": 3,
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Informe: Bearer <JWT>",
            }
        },
    }

    @flask_app.before_request
    def normalize_authorization_header():
        """Aceita JWT puro do Swagger e o formato HTTP Bearer padrão."""
        authorization = request.headers.get("Authorization")
        if authorization and not authorization.lower().startswith("bearer "):
            request.environ["HTTP_AUTHORIZATION"] = f"Bearer {authorization}"

    db.init_app(flask_app)

    with flask_app.app_context():
        import app.models

        db.create_all()

    from app.controllers.auth_controller import AuthController
    from app.controllers.cargo_controller import CargoController
    from app.controllers.operacao_controller import OperacaoController
    from app.controllers.produto_controller import ProdutoController
    from app.controllers.usuario_controller import UsuarioController

    flask_app.register_blueprint(
        ProdutoController.blueprint, url_prefix="/api/produtos"
    )
    flask_app.register_blueprint(CargoController.blueprint, url_prefix="/api/cargos")
    flask_app.register_blueprint(
        UsuarioController.blueprint, url_prefix="/api/usuarios"
    )
    flask_app.register_blueprint(OperacaoController.blueprint, url_prefix="/api")
    flask_app.register_blueprint(AuthController.blueprint, url_prefix="/api/auth")

    configurar_logging(flask_app)

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        registrar_erro(flask_app, error)
        return {
            "erro": "Erro interno do servidor.",
            "detalhe": "Consulte o log da aplicação.",
        }, 500

    Swagger(flask_app)

    return flask_app
