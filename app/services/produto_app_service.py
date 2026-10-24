from decimal import Decimal

from sqlalchemy import func, or_

from app import db
from app.dtos.produto_dto import ProdutoRequestDto
from app.models.estoque import Estoque
from app.models.configuracao_regras import ConfiguracaoRegras
from app.models.historico_preco import HistoricoPreco
from app.models.produto import Produto
from app.repositories.produto_repository import ProdutoRepository
from app.services.auditoria_service import registrar_auditoria


class ProdutoAppService:
    def __init__(self, repository=None):
        self.repository = repository or ProdutoRepository()

    def listar(self, filtros=None, limit=100, offset=0):
        return self.repository.listar(filtros, limit=limit, offset=offset)

    def buscar(self, id_produto):
        return self.repository.buscar_por_id(id_produto)

    def criar(self, dados, usuario_id=None):
        produto_dto = ProdutoRequestDto.from_dict(dados)
        self._validar_nao_duplicado(produto_dto.nome, produto_dto.codigo)
        self._validar_margem(produto_dto.custo, produto_dto.preco_atual)
        produto = Produto(
            nome=produto_dto.nome,
            codigo=produto_dto.codigo,
            descricao=produto_dto.descricao,
            categoria=produto_dto.categoria,
            fornecedor=produto_dto.fornecedor,
            custo=produto_dto.custo,
            preco_atual=produto_dto.preco_atual,
            estoque=produto_dto.estoque,
            data_validade=produto_dto.data_validade,
        )
        db.session.add(produto)
        db.session.flush()
        if produto.estoque > 0:
            db.session.add(
                Estoque(
                    id_produto=produto.id_produto,
                    tipo_operacao="ENTRADA",
                    quantidade=produto.estoque,
                    motivo="Estoque inicial no cadastro do produto",
                    usuario_id=usuario_id,
                )
            )
        registrar_auditoria(
            "PRODUTO_CRIADO",
            "Produto",
            usuario_id=usuario_id,
            entidade_id=produto.id_produto,
            detalhes={"nome": produto.nome},
        )
        self.repository.salvar()
        return produto

    def atualizar(self, id_produto, dados, usuario_id=None):
        produto = self.repository.buscar_com_bloqueio(id_produto)
        if not produto:
            return None
        if not isinstance(dados, dict):
            raise ValueError("Os dados do produto devem ser um objeto JSON.")
        nome = str(dados.get("nome", produto.nome) or "").strip()
        if not nome:
            raise ValueError("O nome do produto é obrigatório.")
        codigo = dados.get("codigo", produto.codigo)
        codigo = str(codigo).strip().upper() or None if codigo is not None else None
        self._validar_nao_duplicado(nome, codigo, ignorar_id=id_produto)
        estoque_anterior = Decimal(str(produto.estoque))
        preco_anterior = Decimal(str(produto.preco_atual))
        produto.nome = nome
        for campo in ("custo", "preco_atual", "estoque"):
            if campo in dados:
                try:
                    valor = Decimal(str(dados[campo]))
                except (ArithmeticError, ValueError):
                    raise ValueError(f"{campo} deve ser numérico.") from None
                if not valor.is_finite():
                    raise ValueError(f"{campo} deve ser finito.")
                setattr(produto, campo, valor)
        if produto.custo < 0 or produto.preco_atual <= 0:
            raise ValueError("O custo não pode ser negativo e o preço deve ser positivo.")
        self._validar_margem(produto.custo, produto.preco_atual)
        for campo in ("codigo", "descricao", "categoria", "fornecedor"):
            if campo in dados:
                valor = dados[campo]
                setattr(produto, campo, str(valor).strip() or None if valor is not None else None)
        limites = {
            "codigo": 80,
            "descricao": 1000,
            "categoria": 100,
            "fornecedor": 150,
        }
        for campo, limite in limites.items():
            valor = getattr(produto, campo)
            if valor and len(valor) > limite:
                raise ValueError(f"{campo} deve ter até {limite} caracteres.")
        produto.codigo = codigo
        if produto.estoque < 0:
            raise ValueError("O estoque não pode ser negativo.")
        if produto.estoque != estoque_anterior:
            diferenca_estoque = produto.estoque - estoque_anterior
            db.session.add(
                Estoque(
                    id_produto=produto.id_produto,
                    tipo_operacao=(
                        "ENTRADA" if diferenca_estoque > 0 else "SAIDA"
                    ),
                    quantidade=abs(diferenca_estoque),
                    motivo="Ajuste de estoque pelo cadastro do produto",
                    usuario_id=usuario_id,
                )
            )
        if produto.preco_atual != preco_anterior:
            db.session.add(
                HistoricoPreco(
                    id_produto=produto.id_produto,
                    preco_antigo=preco_anterior,
                    preco_novo=produto.preco_atual,
                    motivo="Atualização do cadastro do produto",
                    usuario_id=usuario_id,
                )
            )
        if "data_validade" in dados:
            produto.data_validade = ProdutoRequestDto._parse_date(
                dados["data_validade"]
            )
        registrar_auditoria(
            "PRODUTO_ATUALIZADO",
            "Produto",
            usuario_id=usuario_id,
            entidade_id=produto.id_produto,
        )
        self.repository.salvar()
        return produto

    def excluir(self, id_produto, usuario_id=None):
        produto = self.buscar(id_produto)
        if not produto:
            return False
        produto.ativo = False
        registrar_auditoria(
            "PRODUTO_DESATIVADO",
            "Produto",
            usuario_id=usuario_id,
            entidade_id=produto.id_produto,
        )
        self.repository.salvar()
        return True

    def _validar_nao_duplicado(self, nome, codigo, ignorar_id=None):
        consulta = Produto.query.filter(Produto.ativo.is_(True))
        if ignorar_id is not None:
            consulta = consulta.filter(Produto.id_produto != ignorar_id)
        condicoes = [func.lower(Produto.nome) == nome.lower()]
        if codigo:
            condicoes.append(func.upper(Produto.codigo) == codigo.upper())
        duplicado = consulta.filter(or_(*condicoes)).first()
        if duplicado:
            raise ValueError("Já existe um produto ativo com esse nome ou código.")

    @staticmethod
    def _validar_margem(custo, preco):
        configuracao = db.session.get(ConfiguracaoRegras, 1)
        margem = (
            Decimal(str(configuracao.margem_minima))
            if configuracao
            else Decimal("15")
        )
        piso = Decimal(str(custo)) * (1 + margem / 100)
        if Decimal(str(preco)) < piso:
            raise ValueError("O preço deve respeitar a margem mínima configurada.")
