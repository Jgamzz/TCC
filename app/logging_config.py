import logging
import os
import traceback
from logging.handlers import RotatingFileHandler

from flask import has_request_context, request

from app import db
from app.models.log_sistema import LogSistema


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            db.session.rollback()
            usuario_id = None
            rota = None
            metodo = None
            if has_request_context():
                rota = request.path
                metodo = request.method
                usuario_id = getattr(getattr(request, "usuario", None), "id", None)

            log = LogSistema(
                nivel=record.levelname,
                mensagem=record.getMessage(),
                modulo=record.module,
                metodo=metodo,
                rota=rota,
                usuario_id=usuario_id,
                stack_trace=(
                    "".join(traceback.format_exception(*record.exc_info))
                    if record.exc_info
                    else None
                ),
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()
            self.handleError(record)


def configurar_logging(app):
    os.makedirs("logs", exist_ok=True)
    arquivo = os.path.join("logs", "app.log")
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    arquivo_handler = RotatingFileHandler(
        arquivo, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    arquivo_handler.setFormatter(formato)
    arquivo_handler.setLevel(logging.INFO)

    banco_handler = DatabaseLogHandler()
    banco_handler.setLevel(logging.ERROR)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(arquivo_handler)
    app.logger.addHandler(banco_handler)
    logging.getLogger("werkzeug").addHandler(arquivo_handler)


def registrar_erro(app, erro):
    app.logger.error(
        "Erro não tratado na API",
        exc_info=(type(erro), erro, erro.__traceback__),
    )
