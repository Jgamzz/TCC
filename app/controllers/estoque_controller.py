from flask import Blueprint, jsonify, request

from app.services.estoque_app_service import EstoqueAppService
from app.services.usuario_service import verificar_permissao

estoque_bp = Blueprint("estoque_bp", __name__)
estoque_service = EstoqueAppService()
_DEFAULT_PAGE_SIZE = 100
_MAX_PAGE_SIZE = 1000


def _pagination_params():
    try:
        limit = int(request.args.get("limit", _DEFAULT_PAGE_SIZE))
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        raise ValueError("limit e offset devem ser números inteiros.")
    if limit < 1 or limit > _MAX_PAGE_SIZE:
        raise ValueError(f"limit deve estar entre 1 e {_MAX_PAGE_SIZE}.")
    if offset < 0:
        raise ValueError("offset não pode ser negativo.")
    return limit, offset


@estoque_bp.get("/")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def listar():
    """Lista as movimentações de estoque."""
    try:
        limit, offset = _pagination_params()
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(
        [
            movimento.to_dict()
            for movimento in estoque_service.listar(limit=limit, offset=offset)
        ]
    )


@estoque_bp.get("/<int:id_estoque>")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def buscar_por_id(id_estoque):
    """Busca uma movimentação pelo ID."""
    movimento = estoque_service.buscar(id_estoque)
    if not movimento:
        return jsonify({"erro": "Movimentação de estoque não encontrada."}), 404
    return jsonify(movimento.to_dict())


@estoque_bp.post("/")
@verificar_permissao(["GERENTE", "ADMIN"])
def cadastrar():
    """
    Registra uma movimentação e atualiza o saldo do produto.
    ---
    tags: [Estoque]
    security: [{Bearer: []}]
    consumes: [application/json]
    parameters:
      - in: body
        name: movimentacao
        required: true
        schema:
          type: object
          required: [id_produto, tipo_operacao, quantidade, motivo]
          properties:
            id_produto: {type: integer, example: 1}
            tipo_operacao: {type: string, enum: [ENTRADA, SAIDA]}
            quantidade: {type: number, example: 10}
            motivo: {type: string, example: Reposição de mercadoria}
    responses:
      201:
        description: Movimentação registrada
      400:
        description: Dados inválidos ou estoque insuficiente
    """
    try:
        movimento = estoque_service.criar(
            request.get_json(silent=True), usuario_id=request.usuario.id
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(movimento.to_dict()), 201


@estoque_bp.put("/<int:id_estoque>")
@verificar_permissao(["GERENTE", "ADMIN"])
def atualizar(id_estoque):
    """Movimentações são imutáveis; registre uma movimentação compensatória."""
    return jsonify(
        {
            "erro": "Movimentações não podem ser alteradas. Registre uma movimentação compensatória."
        }
    ), 409


@estoque_bp.delete("/<int:id_estoque>")
@verificar_permissao(["GERENTE", "ADMIN"])
def deletar(id_estoque):
    """Movimentações são imutáveis e não podem ser removidas."""
    return jsonify({"erro": "Movimentações não podem ser removidas."}), 409


class EstoqueController:
    """Controller HTTP responsável pelo CRUD de movimentações de estoque."""

    blueprint = estoque_bp
    listar = staticmethod(listar)
    buscar_por_id = staticmethod(buscar_por_id)
    cadastrar = staticmethod(cadastrar)
    atualizar = staticmethod(atualizar)
    deletar = staticmethod(deletar)
