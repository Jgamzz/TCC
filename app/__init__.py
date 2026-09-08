from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from app.config import Config

db = SQLAlchemy()

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    flask_app.config['SWAGGER'] = {
        'title': 'SGB Varejo - API TCC',
        'uiversion': 3
    }

    db.init_app(flask_app)

    with flask_app.app_context():
        import app.models

    from app.controllers.produto_controller import produto_bp
    from app.controllers.cargo_controller import cargo_bp
    from app.controllers.usuario_controller import usuario_bp


    flask_app.register_blueprint(produto_bp, url_prefix='/api/produtos')
    flask_app.register_blueprint(cargo_bp, url_prefix='/api/cargos')
    flask_app.register_blueprint(usuario_bp, url_prefix='/api/usuarios')


    Swagger(flask_app)

    return flask_app