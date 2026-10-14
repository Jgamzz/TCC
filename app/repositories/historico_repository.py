from datetime import timezone

from sqlalchemy import select

from app import db
from app.models.estoque import Estoque
from app.models.feedback_cliente import FeedbackCliente
from app.models.historico_preco import HistoricoPreco
from app.models.produto import Produto


class HistoricoRepository:
    """Combina registros persistidos em uma linha do tempo de atividades."""

    @staticmethod
    def _data_iso(data):
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)
        return data.isoformat()

    def listar(self):
        eventos = []

        movimentacoes = db.session.execute(
            select(Estoque, Produto.nome)
            .join(Produto, Estoque.id_produto == Produto.id_produto)
        ).all()
        for movimento, nome_produto in movimentacoes:
            operacao = movimento.tipo_operacao
            eventos.append(
                {
                    "tipo": "ESTOQUE",
                    "data": self._data_iso(movimento.data_operacao),
                    "id_produto": movimento.id_produto,
                    "produto": nome_produto,
                    "tipo_operacao": operacao,
                    "quantidade": float(movimento.quantidade),
                    "motivo": movimento.motivo,
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
                }
            )

        return sorted(eventos, key=lambda evento: evento["data"], reverse=True)
