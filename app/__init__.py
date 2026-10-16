from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(test_config=None):
    from app.logging_config import configurar_logging, registrar_erro

    flask_app = Flask(
        __name__,
        template_folder="../frontend/template",
        static_folder="../frontend/static",
    )
    flask_app.config.from_object(Config)
    if test_config:
        flask_app.config.update(test_config)
    if not flask_app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("Defina JWT_SECRET_KEY antes de iniciar a aplicação.")
    jwt.init_app(flask_app)

    @flask_app.route("/")
    def index():
        return render_template("index.html")

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

        from app.migrations import migrate_database

        migrate_database(flask_app)

    from app.controllers.auth_controller import AuthController
    from app.controllers.cargo_controller import CargoController
    from app.controllers.estoque_controller import EstoqueController
    from app.controllers.operacao_controller import OperacaoController
    from app.controllers.produto_controller import ProdutoController
    from app.controllers.usuario_controller import UsuarioController

    flask_app.register_blueprint(
        ProdutoController.blueprint, url_prefix="/api/produtos"
    )
    flask_app.register_blueprint(CargoController.blueprint, url_prefix="/api/cargos")
    flask_app.register_blueprint(
        EstoqueController.blueprint, url_prefix="/api/estoque"
    )
    flask_app.register_blueprint(
        UsuarioController.blueprint, url_prefix="/api/usuarios"
    )
    flask_app.register_blueprint(OperacaoController.blueprint, url_prefix="/api")
    flask_app.register_blueprint(AuthController.blueprint, url_prefix="/api/auth")

    @flask_app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            db.session.rollback()
            flask_app.logger.error("Verificação de saúde do banco falhou: %s", error)
            return {"status": "indisponível"}, 503
        return {"status": "ok"}, 200

    configurar_logging(flask_app)

    with flask_app.app_context():
        from app.repositories.planilha_concorrente_repository import (
            PlanilhaConcorrenteRepository,
        )

        arquivos, registros = PlanilhaConcorrenteRepository().sincronizar()
        flask_app.logger.info(
            "Planilhas de concorrência sincronizadas: %s arquivo(s), %s produto(s).",
            arquivos,
            registros,
        )

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error):
        return error

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
