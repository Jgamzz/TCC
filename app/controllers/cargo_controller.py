from flask import Blueprint, jsonify, request
from app.services.cargo_service import CargoService

cargo_bp = Blueprint('cargo_bp', __name__)

@cargo_bp.route('/', methods=['GET'])
def listar():
    """
    Listar todos os cargos
    ---
    tags:
      - Cargos
    responses:
      200:
        description: Lista de cargos retornada com sucesso
    """
    cargos = CargoService.listar_todos()
    return jsonify([c.to_dict() for c in cargos]), 200


@cargo_bp.route('/<int:id_cargo>', methods=['GET'])
def buscar_por_id(id_cargo):
    """
    Buscar um cargo pelo ID
    ---
    tags:
      - Cargos
    parameters:
      - name: id_cargo
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Cargo encontrado
      404:
        description: Cargo não encontrado
    """
    cargo = CargoService.buscar_por_id(id_cargo)
    if not cargo:
        return jsonify({"erro": "Cargo não encontrado"}), 404
    return jsonify(cargo.to_dict()), 200
