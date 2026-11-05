from app import db
from app.models.auditoria import Auditoria


def registrar_auditoria(
    acao, entidade, usuario_id=None, entidade_id=None, detalhes=None
):
    evento = Auditoria(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        detalhes=detalhes,
    )
    db.session.add(evento)
    return evento
