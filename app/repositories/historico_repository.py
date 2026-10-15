from datetime import timezone

from sqlalchemy import inspect, select

from app import db
from app.models.estoque import Estoque
from app.models.auditoria import Auditoria
from app.models.feedback_cliente import FeedbackCliente
from app.models.historico_preco import HistoricoPreco
from app.models.produto import Produto
from app.models.usuario import Usuario


class HistoricoRepository:
    """Combina registros persistidos em uma linha do tempo de atividades."""

    @staticmethod
    def _data_iso(data):
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)
        return data.isoformat()

    def listar(self):
        eventos = []
        usuarios = {
            usuario.id: usuario.name
            for usuario in db.session.execute(select(Usuario)).scalars()
        }
        produtos = {
            str(produto.id_produto): produto.nome
            for produto in db.session.execute(select(Produto)).scalars()
        }
        atores_feedback = {
            auditoria.entidade_id: auditoria.usuario_id
            for auditoria in db.session.execute(
                select(Auditoria).where(Auditoria.acao == "FEEDBACK_REGISTRADO")
            ).scalars()
        }

        inspector = inspect(db.engine)
        nome_tabela_estoque = next(
            (
                name
                for name in inspector.get_table_names()
                if name.lower() == Estoque.__tablename__.lower()
            ),
            Estoque.__tablename__,
        )
        estoque_columns = {
            column["name"].lower()
            for column in inspector.get_columns(nome_tabela_estoque)
        }
        colunas_movimentacao = [
            Estoque.id_estoque,
            Estoque.id_produto,
            Estoque.tipo_operacao,
            Estoque.quantidade,
            Estoque.motivo,
            Estoque.data_operacao,
        ]
        possui_responsavel_estoque = "usuario_id" in estoque_columns
        if possui_responsavel_estoque:
            colunas_movimentacao.append(Estoque.usuario_id)

        movimentacoes = db.session.execute(
            select(*colunas_movimentacao, Produto.nome).join(
                Produto, Estoque.id_produto == Produto.id_produto
            )
        ).all()
        for linha in movimentacoes:
            id_estoque, id_produto, operacao, quantidade, motivo, data_operacao = linha[:6]
            usuario_id = linha[6] if possui_responsavel_estoque else None
            nome_produto = linha[-1]
            eventos.append(
                {
                    "tipo": "ESTOQUE",
                    "data": self._data_iso(data_operacao),
                    "id_produto": id_produto,
                    "produto": nome_produto,
                    "tipo_operacao": operacao,
                    "quantidade": float(quantidade),
                    "motivo": motivo,
                    "usuario_id": usuario_id,
                    "usuario_nome": usuarios.get(usuario_id),
                    "responsavel_registrado": possui_responsavel_estoque,
                }
            )

        feedbacks = db.session.execute(
            select(FeedbackCliente, Produto.nome)
            .join(Produto, FeedbackCliente.id_produto == Produto.id_produto)
        ).all()
        for feedback, nome_produto in feedbacks:
            eventos.append(
                {
                    "tipo": "FEEDBACK",
                    "data": self._data_iso(feedback.data_criacao),
                    "id_produto": feedback.id_produto,
                    "produto": nome_produto,
                    "cliente": feedback.cliente,
                    "mensagem": feedback.comentario,
                    "usuario_id": atores_feedback.get(str(feedback.id_feedback)),
                    "usuario_nome": usuarios.get(
                        atores_feedback.get(str(feedback.id_feedback))
                    ),
                }
            )

        alteracoes_preco = db.session.execute(
            select(HistoricoPreco, Produto.nome)
            .join(Produto, HistoricoPreco.id_produto == Produto.id_produto)
        ).all()
        for alteracao, nome_produto in alteracoes_preco:
            eventos.append(
                {
                    "tipo": "PRECO",
                    "data": self._data_iso(alteracao.data_alteracao),
                    "id_produto": alteracao.id_produto,
                    "produto": nome_produto,
                    "preco_antigo": float(alteracao.preco_antigo),
                    "preco_novo": float(alteracao.preco_novo),
                    "motivo": alteracao.motivo,
                    "usuario_id": alteracao.usuario_id,
                    "usuario_nome": usuarios.get(alteracao.usuario_id),
                }
            )

        eventos_representados = {
            "ESTOQUE_MOVIMENTADO",
            "VENDA_REGISTRADA",
            "FEEDBACK_REGISTRADO",
        }
        auditorias = db.session.execute(
            select(Auditoria).order_by(Auditoria.data_criacao.desc())
        ).scalars()
        for auditoria in auditorias:
            if auditoria.acao in eventos_representados:
                continue
            detalhes = auditoria.detalhes or {}
            entidade = auditoria.entidade
            if entidade == "Produto":
                entidade = produtos.get(auditoria.entidade_id, entidade)
            elif entidade in {"SugestaoPreco", "PrecoConcorrente"}:
                id_produto = detalhes.get("id_produto")
                entidade = produtos.get(
                    str(id_produto),
                    "Sugestão de preço"
                    if entidade == "SugestaoPreco"
                    else "Preço de concorrente",
                )
            elif entidade == "Usuario":
                entidade = (
                    detalhes.get("username")
                    or usuarios.get(auditoria.usuario_id)
                    or entidade
                )
            eventos.append(
                {
                    "tipo": "ATIVIDADE",
                    "data": self._data_iso(auditoria.data_criacao),
                    "id_produto": None,
                    "produto": entidade,
                    "acao": auditoria.acao,
                    "usuario_id": auditoria.usuario_id,
                    "usuario_nome": usuarios.get(auditoria.usuario_id),
                    "mensagem": detalhes,
                }
            )

        return sorted(eventos, key=lambda evento: evento["data"], reverse=True)
