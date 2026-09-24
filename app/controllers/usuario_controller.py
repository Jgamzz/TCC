from flask import Blueprint, jsonify, request
from app.services.usuario_service import UsuarioService
from app.services.usuario_service import verificar_permissao

usuario_bp = Blueprint("usuario_bp", __name__)


@usuario_bp.route("/", methods=["GET"])
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def listar():
    """
    Listar todos os usuários
    ---
    tags:
      - Usuários
    responses:
      200:
        description: Lista de usuários cadastrados
    """
    usuarios = UsuarioService.listar_todos()
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuario_bp.route("/<int:id_usuario>", methods=["GET"])
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def buscar_por_id(id_usuario):
    """
    Buscar usuário pelo ID
    ---
    tags:
      - Usuários
    parameters:
      - name: id_usuario
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Usuário encontrado
      404:
        description: Usuário não encontrado
    """
    usuario = UsuarioService.buscar_por_id(id_usuario)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify(usuario.to_dict()), 200


@usuario_bp.route("/", methods=["POST"])
@verificar_permissao(["ADMIN"])
def cadastrar():
    """
    Cadastrar um novo usuário
    ---
    tags:
      - Usuários
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - Username
            - Password
            - Name
          properties:
            Username:
              type: string
              example: "joao.silva"
            Password:
              type: string
              example: "123456"
            Name:
              type: string
              example: "João Silva"
            Is_Active:
              type: boolean
              example: true
            Cargo_ID:
              type: integer
              example: 1
    responses:
      201:
        description: Usuário cadastrado com sucesso
      400:
        description: Erro nos dados fornecidos
    """
    dados = request.get_json()
    try:
        novo_usuario = UsuarioService.criar_usuario(dados)
        return jsonify(novo_usuario.to_dict()), 201
    except ValueError as ve:
        return jsonify({"erro": str(ve)}), 400
    except Exception as e:
        return jsonify({"erro": "Erro ao criar usuário"}), 500


@usuario_bp.route("/<int:id_usuario>", methods=["PUT"])
@verificar_permissao(["GERENTE", "ADMIN"])
def atualizar(id_usuario):
    """
    Atualizar um usuário existente
    ---
    tags:
      - Usuários
    parameters:
      - name: id_usuario
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            Username:
              type: string
              example: "joao.silva"
            Password:
              type: string
              example: "nova_senha123"
            Name:
              type: string
              example: "João da Silva"
            Is_Active:
              type: boolean
              example: true
            Cargo_ID:
              type: integer
              example: 2
    responses:
      200:
        description: Usuário atualizado com sucesso
      404:
        description: Usuário não encontrado
    """
    dados = request.get_json()
    try:
        usuario = UsuarioService.atualizar_usuario(id_usuario, dados)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify(usuario.to_dict()), 200
    except ValueError as ve:
        return jsonify({"erro": str(ve)}), 400


@usuario_bp.route("/<int:id_usuario>", methods=["DELETE"])
@verificar_permissao(["GERENTE", "ADMIN"])
def deletar(id_usuario):
    """
    Remover um usuário pelo ID
    ---
    tags:
      - Usuários
    parameters:
      - name: id_usuario
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Usuário removido com sucesso
      404:
        description: Usuário não encontrado
    """
    sucesso = UsuarioService.deletar_usuario(id_usuario)
    if not sucesso:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"mensagem": f"Usuário {id_usuario} removido com sucesso"}), 200


class UsuarioController:
    """Controller HTTP responsável pelo gerenciamento de usuários."""

    blueprint = usuario_bp
    listar = staticmethod(listar)
    buscar_por_id = staticmethod(buscar_por_id)
    cadastrar = staticmethod(cadastrar)
    atualizar = staticmethod(atualizar)
    deletar = staticmethod(deletar)
