from flask import Blueprint, jsonify, request

from app.dtos.produto_dto import ProdutoResponseDto
from app.services.produto_app_service import ProdutoAppService
from app.services.usuario_service import verificar_permissao

produto_bp = Blueprint("produto_bp", __name__)
produto_service = ProdutoAppService()


@produto_bp.get("/")
@verificar_permissao(["FUNCIONARIO", "GERENTE", "DONO"])
def listar():
    """
    Lista produtos.
    ---
    tags: [Produtos]
    security: [{Bearer: []}]
    responses:
      200:
        description: Produtos encontrados
      401:
        description: Token ausente ou inválido
    """
    return jsonify(
        [
            ProdutoResponseDto.from_model(produto).to_dict()
            for produto in produto_service.listar()
        ]
    )


@produto_bp.get("/<int:id_produto>")
@verificar_permissao(["FUNCIONARIO", "GERENTE", "DONO"])
def buscar_por_id(id_produto):
    """
    Busca um produto pelo ID.
    ---
    tags: [Produtos]
    security: [{Bearer: []}]
    parameters:
      - name: id_produto
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Produto encontrado
      404:
        description: Produto não encontrado
    """
    produto = produto_service.buscar(id_produto)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify(ProdutoResponseDto.from_model(produto).to_dict())


@produto_bp.post("/")
@verificar_permissao(["DONO"])
def cadastrar():
    """
    Cadastra um produto. Apenas o dono.
    ---
    tags: [Produtos]
    security: [{Bearer: []}]
    consumes: [application/json]
    parameters:
      - in: body
        name: produto
        required: true
        schema:
          type: object
          required: [nome, custo, preco_atual]
          properties:
            nome: {type: string, example: Arroz 5kg}
            custo: {type: number, example: 18.50}
            preco_atual: {type: number, example: 25.00}
            estoque: {type: number, example: 50}
            data_validade: {type: string, format: date, example: '2026-12-31'}
    responses:
      201:
        description: Produto criado
      403:
        description: Permissão negada
    """
    try:
        produto = produto_service.criar(request.get_json(silent=True))
        return jsonify(ProdutoResponseDto.from_model(produto).to_dict()), 201
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400


@produto_bp.put("/<int:id_produto>")
@verificar_permissao(["GERENTE", "DONO"])
def atualizar(id_produto):
    """
    Atualiza um produto. Gerente ou dono.
    ---
    tags: [Produtos]
    security: [{Bearer: []}]
    parameters:
      - name: id_produto
        in: path
        required: true
        type: integer
      - in: body
        name: produto
        required: true
        schema: {type: object}
    responses:
      200:
        description: Produto atualizado
      404:
        description: Produto não encontrado
    """
    try:
        produto = produto_service.atualizar(id_produto, request.get_json(silent=True))
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify(ProdutoResponseDto.from_model(produto).to_dict())


@produto_bp.delete("/<int:id_produto>")
@verificar_permissao(["GERENTE", "DONO"])
def deletar(id_produto):
    """
    Exclui um produto. Gerente ou dono.
    ---
    tags: [Produtos]
    security: [{Bearer: []}]
    parameters:
      - name: id_produto
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Produto removido
      404:
        description: Produto não encontrado
    """
    if not produto_service.excluir(id_produto):
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({"mensagem": "Produto removido com sucesso"})


class ProdutoController:
    """Controller HTTP responsável pelo gerenciamento de produtos."""

    blueprint = produto_bp
    listar = staticmethod(listar)
    buscar_por_id = staticmethod(buscar_por_id)
    cadastrar = staticmethod(cadastrar)
    atualizar = staticmethod(atualizar)
    deletar = staticmethod(deletar)
