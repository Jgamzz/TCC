from flask import Blueprint, jsonify, request

from app.services.estoque_app_service import EstoqueAppService
from app.services.usuario_service import verificar_permissao

estoque_bp = Blueprint("estoque_bp", __name__)
estoque_service = EstoqueAppService()


@estoque_bp.get("/")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def listar():
    """Lista as movimentações de estoque."""
    return jsonify([movimento.to_dict() for movimento in estoque_service.listar()])


@estoque_bp.get("/<int:id_estoque>")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def buscar_por_id(id_estoque):
    """Busca uma movimentação pelo ID."""
    movimento = estoque_service.buscar(id_estoque)
    if not movimento:
        return jsonify({"erro": "Movimentação de estoque não encontrada."}), 404
    return jsonify(movimento.to_dict())


@estoque_bp.post("/")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
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
        movimento = estoque_service.criar(request.get_json(silent=True))
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(movimento.to_dict()), 201


@estoque_bp.put("/<int:id_estoque>")
@verificar_permissao(["GERENTE", "ADMIN"])
def atualizar(id_estoque):
    """Atualiza uma movimentação e recalcula o saldo do produto."""
    try:
        movimento = estoque_service.atualizar(
            id_estoque, request.get_json(silent=True)
        )
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if not movimento:
        return jsonify({"erro": "Movimentação de estoque não encontrada."}), 404
    return jsonify(movimento.to_dict())


@estoque_bp.delete("/<int:id_estoque>")
@verificar_permissao(["GERENTE", "ADMIN"])
def deletar(id_estoque):
    """Exclui uma movimentação e reverte seu impacto no saldo."""
    try:
        excluido = estoque_service.excluir(id_estoque)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if not excluido:
        return jsonify({"erro": "Movimentação de estoque não encontrada."}), 404
    return jsonify({"mensagem": "Movimentação de estoque removida com sucesso."})


class EstoqueController:
    """Controller HTTP responsável pelo CRUD de movimentações de estoque."""

    blueprint = estoque_bp
    listar = staticmethod(listar)
    buscar_por_id = staticmethod(buscar_por_id)
    cadastrar = staticmethod(cadastrar)
    atualizar = staticmethod(atualizar)
    deletar = staticmethod(deletar)
