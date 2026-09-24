from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.estoque_app_service import EstoqueAppService
from app.services.precificacao_app_service import PrecificacaoAppService
from app.services.usuario_service import verificar_permissao

operacao_bp = Blueprint("operacao_bp", __name__)
estoque_service = EstoqueAppService()
preco_service = PrecificacaoAppService()


@operacao_bp.post("/vendas")
@verificar_permissao(["GERENTE", "ADMIN"])
def registrar_venda():
    """
    Registra uma venda e reduz o estoque.
    ---
    tags: [Operações]
    security: [{Bearer: []}]
    consumes: [application/json]
    parameters:
      - in: body
        name: venda
        required: true
        schema:
          type: object
          required: [id_produto, quantidade]
          properties:
            id_produto: {type: integer, example: 1}
            quantidade: {type: number, example: 2}
    responses:
      201:
        description: Venda registrada
    """
    dados = request.get_json(silent=True) or {}
    try:
        venda = estoque_service.registrar_venda(
            dados["id_produto"],
            dados["quantidade"],
            (
                datetime.fromisoformat(dados["data_venda"])
                if dados.get("data_venda")
                else None
            ),
        )
        return jsonify(venda.to_dict()), 201
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


@operacao_bp.post("/concorrentes")
@verificar_permissao(["GERENTE", "ADMIN"])
def registrar_concorrente():
    """
    Registra o preço de um concorrente.
    ---
    tags: [Operações]
    security: [{Bearer: []}]
    responses:
      201:
        description: Preço registrado
    """
    dados = request.get_json(silent=True) or {}
    try:
        preco = preco_service.registrar_preco_concorrente(
            dados["id_produto"], dados["valor"]
        )
        return jsonify(preco.to_dict()), 201
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


@operacao_bp.post("/feedbacks")
@verificar_permissao(["GERENTE", "ADMIN"])
def registrar_feedback():
    """
    Registra um feedback de cliente.
    ---
    tags: [Operações]
    security: [{Bearer: []}]
    responses:
      201:
        description: Feedback registrado
    """
    dados = request.get_json(silent=True) or {}
    try:
        feedback = preco_service.registrar_feedback(
            dados["id_produto"], dados["comentario"], dados.get("cliente")
        )
        return jsonify(feedback.to_dict()), 201
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


@operacao_bp.post("/sugestoes")
@verificar_permissao(["GERENTE", "ADMIN"])
def gerar_sugestao():
    """
    Gera uma sugestão de preço pelo motor de regras.
    ---
    tags: [Precificação]
    security: [{Bearer: []}]
    responses:
      201:
        description: Sugestão criada
    """
    dados = request.get_json(silent=True) or {}
    try:
        sugestao = preco_service.gerar_sugestao(
            dados["id_produto"], request.usuario.id, dados.get("feedback_cliente")
        )
        return jsonify(sugestao.to_dict()), 201
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


@operacao_bp.get("/sugestoes")
@verificar_permissao(["GERENTE", "ADMIN"])
def listar_sugestoes():
    """
    Lista sugestões pendentes para aprovação.
    ---
    tags: [Precificação]
    security: [{Bearer: []}]
    responses:
      200:
        description: Sugestões pendentes
    """
    return jsonify(
        [sugestao.to_dict() for sugestao in preco_service.listar_pendentes()]
    )


@operacao_bp.patch("/sugestoes/<int:id_sugestao>")
@verificar_permissao(["GERENTE", "ADMIN"])
def decidir_sugestao(id_sugestao):
    """
    Aprova, edita ou rejeita uma sugestão.
    ---
    tags: [Precificação]
    security: [{Bearer: []}]
    parameters:
      - name: id_sugestao
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Decisão registrada
    """
    dados = request.get_json(silent=True) or {}
    try:
        sugestao = preco_service.decidir_sugestao(
            id_sugestao,
            dados["decisao"],
            request.usuario.id,
            dados.get("preco"),
            dados.get("observacao"),
        )
        return jsonify(sugestao.to_dict())
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


class OperacaoController:
    """Controller HTTP das operações de estoque e precificação."""

    blueprint = operacao_bp
    registrar_venda = staticmethod(registrar_venda)
    registrar_concorrente = staticmethod(registrar_concorrente)
    registrar_feedback = staticmethod(registrar_feedback)
    gerar_sugestao = staticmethod(gerar_sugestao)
    listar_sugestoes = staticmethod(listar_sugestoes)
    decidir_sugestao = staticmethod(decidir_sugestao)
