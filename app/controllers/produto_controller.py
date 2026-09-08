from flask import Blueprint, jsonify, request
from app.services.produto_service import ProdutoService
from app.services.usuario_service import verificar_permissao

produto_bp = Blueprint('produto_bp', __name__)

# Cargo 1: Funcionário | Cargo 2: Gerente | Cargo 3: Dono

@produto_bp.route('/', methods=['GET'])
@verificar_permissao([1, 2, 3])  # Todos podem visualizar
def listar():
    """
    Listar todos os produtos (Funcionário, Gerente e Dono)
    ---
    tags:
      - Produtos
    parameters:
      - name: X-User-ID
        in: header
        type: integer
        required: true
        description: ID do Usuário logado
    responses:
      200:
        description: Lista de produtos retornada com sucesso
      403:
        description: Permissão negada
    """
    produtos = ProdutoService.listar_todos()
    return jsonify([p.to_dict() for p in produtos]), 200


@produto_bp.route('/<int:id_produto>', methods=['GET'])
@verificar_permissao([1, 2, 3])  # Todos podem visualizar
def buscar_por_id(id_produto):
    """
    Buscar produto por ID (Funcionário, Gerente e Dono)
    ---
    tags:
      - Produtos
    parameters:
      - name: X-User-ID
        in: header
        type: integer
        required: true
        description: ID do Usuário logado
      - name: id_produto
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Produto encontrado
      404:
        description: Produto não encontrado
    """
    produto = ProdutoService.buscar_por_id(id_produto)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify(produto.to_dict()), 200


@produto_bp.route('/', methods=['POST'])
@verificar_permissao([2, 3])  # Apenas Gerente e Dono
def cadastrar():
    """
    Cadastrar um novo produto (Apenas Gerente e Dono)
    ---
    tags:
      - Produtos
    parameters:
      - name: X-User-ID
        in: header
        type: integer
        required: true
        description: ID do Usuário logado
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nome
            - custo
            - preco_atual
          properties:
            nome:
              type: string
              example: "Arroz 5kg"
            custo:
              type: number
              example: 18.50
            preco_atual:
              type: number
              example: 25.00
            estoque:
              type: number
              example: 50
    responses:
      201:
        description: Produto criado com sucesso
      403:
        description: Acesso proibido para o cargo atual
    """
    dados = request.get_json()
    novo_produto = ProdutoService.criar_produto(dados)
    return jsonify(novo_produto.to_dict()), 201


@produto_bp.route('/<int:id_produto>', methods=['PUT'])
@verificar_permissao([2, 3])  # Apenas Gerente e Dono
def atualizar(id_produto):
    """
    Atualizar um produto (Apenas Gerente e Dono)
    ---
    tags:
      - Produtos
    parameters:
      - name: X-User-ID
        in: header
        type: integer
        required: true
        description: ID do Usuário logado
      - name: id_produto
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nome:
              type: string
              example: "Arroz 5kg Tipo 1"
            custo:
              type: number
              example: 19.00
            preco_atual:
              type: number
              example: 26.50
            estoque:
              type: number
              example: 45
    responses:
      200:
        description: Produto atualizado com sucesso
      403:
        description: Acesso proibido para o cargo atual
    """
    dados = request.get_json()
    produto_atualizado = ProdutoService.atualizar_produto(id_produto, dados)
    if not produto_atualizado:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify(produto_atualizado.to_dict()), 200


@produto_bp.route('/<int:id_produto>', methods=['DELETE'])
@verificar_permissao([3])  # Apenas o Dono
def deletar(id_produto):
    """
    Deletar um produto (Apenas Dono)
    ---
    tags:
      - Produtos
    parameters:
      - name: X-User-ID
        in: header
        type: integer
        required: true
        description: ID do Usuário logado
      - name: id_produto
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Produto removido com sucesso
      403:
        description: Apenas o Dono pode excluir produtos
    """
    sucesso = ProdutoService.deletar_produto(id_produto)
    if not sucesso:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({"mensagem": f"Produto {id_produto} removido com sucesso"}), 200