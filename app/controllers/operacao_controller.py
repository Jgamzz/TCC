from datetime import datetime
from datetime import timedelta

from flask import Blueprint, jsonify, request
from app import db
from sqlalchemy import func

from app.services.estoque_app_service import EstoqueAppService
from app.services.usuario_service import verificar_permissao
from app.services.precificacao_app_service import PrecificacaoAppService
from app.repositories.historico_repository import HistoricoRepository
from app.repositories.planilha_concorrente_repository import (
    PlanilhaConcorrenteRepository,
)
from app.services.auditoria_service import registrar_auditoria
from app.models.historico_preco import HistoricoPreco
from app.models.produto import Produto
from app.models.venda import Venda

operacao_bp = Blueprint("operacao_bp", __name__)
estoque_service = EstoqueAppService()
preco_service = PrecificacaoAppService()
planilhas_concorrentes = PlanilhaConcorrenteRepository()
historico_repository = HistoricoRepository()


def _json_object():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}


@operacao_bp.get("/historico")
@verificar_permissao(["GERENTE", "ADMIN"])
def listar_historico():
    """Retorna feedbacks, movimentações de estoque e alterações de preço."""
    return jsonify(historico_repository.listar())


@operacao_bp.get("/giro")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def consultar_giro_catalogo():
    """Retorna unidades vendidas por produto nos últimos 7 e 30 dias."""
    return jsonify(preco_service.consultar_giro_catalogo())


@operacao_bp.get("/concorrentes/planilhas")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
def listar_planilhas_concorrentes():
    """Retorna preços importados das planilhas para comparação."""
    return jsonify(planilhas_concorrentes.listar_comparacao())


@operacao_bp.get("/configuracoes")
@verificar_permissao(["ADMIN"])
def obter_configuracoes():
    return jsonify(preco_service.obter_configuracao().to_dict())


@operacao_bp.put("/configuracoes")
@verificar_permissao(["ADMIN"])
def salvar_configuracoes():
    dados = _json_object()
    try:
        configuracao = preco_service.salvar_configuracao(dados, request.usuario.id)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    return jsonify(configuracao.to_dict())


@operacao_bp.get("/relatorios")
@verificar_permissao(["GERENTE", "ADMIN"])
def gerar_relatorio():
    tipo = request.args.get("tipo", "").strip().lower()
    try:
        inicio = datetime.fromisoformat(request.args["inicio"]).date()
        fim = datetime.fromisoformat(request.args["fim"]).date()
    except (KeyError, TypeError, ValueError):
        return jsonify({"erro": "Informe início e fim no formato AAAA-MM-DD."}), 400
    if inicio > fim:
        return jsonify({"erro": "A data inicial não pode ser posterior à final."}), 400
    if (fim - inicio).days > 3660:
        return jsonify({"erro": "O período máximo permitido é de 10 anos."}), 400
    inicio_dt = datetime.combine(inicio, datetime.min.time())
    fim_dt = datetime.combine(fim + timedelta(days=1), datetime.min.time())

    if tipo == "vendas":
        linhas = (
            db.session.query(
                Produto.id_produto,
                Produto.nome,
                func.coalesce(func.sum(Venda.quantidade), 0),
                func.coalesce(
                    func.sum(Venda.quantidade * Venda.preco_unitario), 0
                ),
            )
            .outerjoin(
                Venda,
                (Venda.id_produto == Produto.id_produto)
                & (Venda.data_venda >= inicio_dt)
                & (Venda.data_venda < fim_dt),
            )
            .filter(Produto.ativo.is_(True))
            .group_by(Produto.id_produto, Produto.nome)
            .order_by(Produto.nome)
            .all()
        )
        return jsonify(
            {
                "tipo": tipo,
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "dados": [
                    {
                        "id_produto": row[0],
                        "produto": row[1],
                        "quantidade": float(row[2]),
                        "faturamento": float(row[3]),
                    }
                    for row in linhas
                ],
            }
        )
    if tipo == "giro":
        linhas = (
            db.session.query(
                Produto.id_produto,
                Produto.nome,
                Produto.estoque,
                func.coalesce(func.sum(Venda.quantidade), 0),
            )
            .outerjoin(
                Venda,
                (Venda.id_produto == Produto.id_produto)
                & (Venda.data_venda >= inicio_dt)
                & (Venda.data_venda < fim_dt),
            )
            .filter(Produto.ativo.is_(True))
            .group_by(Produto.id_produto, Produto.nome, Produto.estoque)
            .order_by(Produto.nome)
            .all()
        )
        return jsonify(
            {
                "tipo": tipo,
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "dados": [
                    {
                        "id_produto": row[0],
                        "produto": row[1],
                        "estoque_atual": float(row[2]),
                        "quantidade_vendida": float(row[3]),
                    }
                    for row in linhas
                ],
            }
        )
    if tipo == "precos":
        alteracoes = (
            db.session.query(HistoricoPreco, Produto.nome)
            .join(Produto, Produto.id_produto == HistoricoPreco.id_produto)
            .filter(
                HistoricoPreco.data_alteracao >= inicio_dt,
                HistoricoPreco.data_alteracao < fim_dt,
            )
            .order_by(HistoricoPreco.data_alteracao.desc())
            .all()
        )
        return jsonify(
            {
                "tipo": tipo,
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "dados": [
                    {
                        "produto": nome,
                        **registro.to_dict(),
                    }
                    for registro, nome in alteracoes
                ],
            }
        )
    return jsonify({"erro": "tipo deve ser vendas, giro ou precos."}), 400


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
    dados = _json_object()
    try:
        venda = estoque_service.registrar_venda(
            dados["id_produto"],
            dados["quantidade"],
            (
                datetime.fromisoformat(dados["data_venda"])
                if dados.get("data_venda")
                else None
            ),
            usuario_id=request.usuario.id,
            motivo=dados.get("motivo"),
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
    dados = _json_object()
    try:
        preco = preco_service.registrar_preco_concorrente(
            dados["id_produto"],
            dados["valor"],
            dados.get("concorrente"),
            usuario_id=request.usuario.id,
        )
        return jsonify(preco.to_dict()), 201
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


@operacao_bp.post("/feedbacks")
@verificar_permissao(["USUARIO", "GERENTE", "ADMIN"])
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
    dados = _json_object()
    try:
        feedback = preco_service.registrar_feedback(
            dados["id_produto"],
            dados["comentario"],
            dados.get("cliente"),
            usuario_id=request.usuario.id,
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
        registrar_auditoria(
            "SUGESTAO_GERADA",
            "SugestaoPreco",
            usuario_id=request.usuario.id,
            entidade_id=sugestao.id_sugestao,
            detalhes={
                "id_produto": sugestao.id_produto,
                "preco_atual": str(sugestao.preco_atual),
                "preco_sugerido": str(sugestao.preco_sugerido),
                "motivo": sugestao.motivo,
            },
        )
        db.session.commit()
        return jsonify(sugestao.to_dict()), 201
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


@operacao_bp.post("/sugestoes/lote")
@verificar_permissao(["GERENTE", "ADMIN"])
def gerar_sugestoes_catalogo():
    try:
        sugestoes = preco_service.gerar_sugestoes_catalogo(request.usuario.id)
        registrar_auditoria(
            "SUGESTOES_CATALOGO_GERADAS",
            "SugestaoPreco",
            usuario_id=request.usuario.id,
            detalhes={"quantidade": len(sugestoes)},
        )
        db.session.commit()
        return jsonify([sugestao.to_dict() for sugestao in sugestoes]), 201
    except ValueError as erro:
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
        registrar_auditoria(
            "SUGESTAO_DECIDIDA",
            "SugestaoPreco",
            usuario_id=request.usuario.id,
            entidade_id=sugestao.id_sugestao,
            detalhes={
                "decisao": sugestao.status,
                "id_produto": sugestao.id_produto,
                "preco_atual": str(sugestao.preco_atual),
                "preco_final": str(sugestao.preco_sugerido),
                "observacao": sugestao.observacao_aprovacao,
            },
        )
        db.session.commit()
        return jsonify(sugestao.to_dict())
    except (KeyError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400


class OperacaoController:
    """Controller HTTP das operações de estoque e precificação."""

    blueprint = operacao_bp
    listar_historico = staticmethod(listar_historico)
    consultar_giro_catalogo = staticmethod(consultar_giro_catalogo)
    registrar_venda = staticmethod(registrar_venda)
    registrar_concorrente = staticmethod(registrar_concorrente)
    registrar_feedback = staticmethod(registrar_feedback)
    gerar_sugestao = staticmethod(gerar_sugestao)
    gerar_sugestoes_catalogo = staticmethod(gerar_sugestoes_catalogo)
    listar_sugestoes = staticmethod(listar_sugestoes)
    decidir_sugestao = staticmethod(decidir_sugestao)
