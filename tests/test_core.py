import time
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, text
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app, db
from app.models.cargo import Cargo
from app.models.configuracao_regras import ConfiguracaoRegras
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.models.venda import Venda
from app.services.auditoria_service import registrar_auditoria
from app.services.precificacao_app_service import PrecificacaoAppService
from app.services.usuario_service import UsuarioService
from app.migrations.manager import _ensure_stock_user_column


class CoreFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "JWT_SECRET_KEY": "unit-test-key-with-more-than-thirty-two-bytes",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            }
        )

    def setUp(self):
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        db.session.add_all(
            [
                Cargo(id=1, name="Admin", is_active=True),
                Cargo(id=2, name="Gerente", is_active=True),
                Cargo(id=3, name="Usuário", is_active=True),
                ConfiguracaoRegras(
                    id_configuracao=1,
                    limiar_giro=10,
                    dias_validade=7,
                    margem_minima=15,
                ),
            ]
        )
        self.admin = self._create_user("admin", "Admin", 1, "admin@example.test")
        self.manager = self._create_user(
            "manager", "Gerente", 2, "manager@example.test"
        )
        self.common = self._create_user("common", "Usuário", 3, "common@example.test")
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    @staticmethod
    def _create_user(username, name, role_id, email):
        user = Usuario(
            username=username,
            name=name,
            email=email,
            password=generate_password_hash("StrongPass123", method="scrypt"),
            is_active=True,
            cargo_id=role_id,
        )
        db.session.add(user)
        return user

    def _token(self, user):
        with self.app.app_context():
            return create_access_token(identity=str(user.id))

    def _headers(self, user):
        return {"Authorization": f"Bearer {self._token(user)}"}

    def _create_product(self, name="Arroz", **overrides):
        data = {
            "nome": name,
            "codigo": f"CODE-{name}",
            "descricao": "Produto de teste",
            "categoria": "Alimentos",
            "fornecedor": "Fornecedor",
            "custo": 10,
            "preco_atual": 20,
            "estoque": 10,
        }
        data.update(overrides)
        response = self.client.post(
            "/api/produtos/", json=data, headers=self._headers(self.admin)
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def test_passwords_are_hashed_and_login_lockout_is_applied(self):
        stored = db.session.get(Usuario, self.manager.id).password
        self.assertNotEqual(stored, "StrongPass123")
        self.assertTrue(check_password_hash(stored, "StrongPass123"))

        for _ in range(5):
            response = self.client.post(
                "/api/auth/login",
                json={"Username": "manager", "Password": "WrongPass123"},
            )
            self.assertEqual(response.status_code, 401)
        blocked = self.client.post(
            "/api/auth/login",
            json={"Username": "manager", "Password": "StrongPass123"},
        )
        self.assertEqual(blocked.status_code, 401)
        self.assertIsNotNone(db.session.get(Usuario, self.manager.id).locked_until)

    def test_common_user_cannot_change_stock_and_manager_can(self):
        product = self._create_product(estoque=5)
        payload = {
            "id_produto": product["id_produto"],
            "tipo_operacao": "ENTRADA",
            "quantidade": 2,
            "motivo": "Reposição",
        }
        forbidden = self.client.post(
            "/api/estoque/", json=payload, headers=self._headers(self.common)
        )
        self.assertEqual(forbidden.status_code, 403)
        created = self.client.post(
            "/api/estoque/", json=payload, headers=self._headers(self.manager)
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        self.assertEqual(
            db.session.get(Produto, product["id_produto"]).estoque, 7
        )

    def test_product_filters_soft_delete_and_immutable_stock_history(self):
        product = self._create_product(
            codigo="A-100", categoria="Mercearia", fornecedor="Mercado X"
        )
        headers = self._headers(self.manager)
        filtered = self.client.get(
            "/api/produtos/?categoria=mercearia&disponivel=true", headers=headers
        )
        self.assertEqual([item["id_produto"] for item in filtered.get_json()], [
            product["id_produto"]
        ])
        forbidden_delete = self.client.delete(
            f"/api/produtos/{product['id_produto']}", headers=headers
        )
        self.assertEqual(forbidden_delete.status_code, 403)

        movement = self.client.post(
            "/api/estoque/",
            json={
                "id_produto": product["id_produto"],
                "tipo_operacao": "ENTRADA",
                "quantidade": 1,
                "motivo": "Reposição",
            },
            headers=headers,
        ).get_json()
        immutable = self.client.delete(
            f"/api/estoque/{movement['id_estoque']}", headers=headers
        )
        self.assertEqual(immutable.status_code, 409)

        deleted = self.client.delete(
            f"/api/produtos/{product['id_produto']}",
            headers=self._headers(self.admin),
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertIsNotNone(db.session.get(Produto, product["id_produto"]))
        self.assertFalse(db.session.get(Produto, product["id_produto"]).ativo)

    def test_history_includes_timestamp_actor_and_stock_activity(self):
        product = self._create_product()
        response = self.client.post(
            "/api/estoque/",
            json={
                "id_produto": product["id_produto"],
                "tipo_operacao": "SAIDA",
                "quantidade": 1,
                "motivo": "Uso de teste",
            },
            headers=self._headers(self.manager),
        )
        self.assertEqual(response.status_code, 201, response.get_json())

        inspector_real = inspect(db.engine)
        with patch("app.repositories.historico_repository.inspect") as inspector_mock:
            inspector_mock.return_value.get_table_names.return_value = (
                inspector_real.get_table_names()
            )
            inspector_mock.return_value.get_columns.side_effect = lambda nome_tabela: [
                coluna
                for coluna in inspector_real.get_columns(nome_tabela)
                if coluna["name"].lower() != "usuario_id"
            ]
            history_legacy = self.client.get(
                "/api/historico", headers=self._headers(self.manager)
            )

        self.assertEqual(history_legacy.status_code, 200, history_legacy.get_json())
        legacy_event = next(
            item
            for item in history_legacy.get_json()
            if item["tipo"] == "ESTOQUE" and item["motivo"] == "Uso de teste"
        )
        self.assertFalse(legacy_event["responsavel_registrado"])

        history = self.client.get(
            "/api/historico", headers=self._headers(self.manager)
        )

        self.assertEqual(history.status_code, 200, history.get_json())
        event = next(
            item
            for item in history.get_json()
            if item["tipo"] == "ESTOQUE"
            and item["motivo"] == "Uso de teste"
        )
        self.assertTrue(event["data"])
        self.assertEqual(event["usuario_nome"], "Gerente")
        self.assertEqual(event["produto"], product["nome"])

    def test_legacy_stock_table_migration_adds_user_column(self):
        engine = create_engine("sqlite:///:memory:")
        try:
            with engine.begin() as connection:
                connection.execute(text('CREATE TABLE "Estoque" (id INTEGER PRIMARY KEY)'))
                _ensure_stock_user_column(connection)
                columns = {
                    column["name"]
                    for column in inspect(connection).get_columns("Estoque")
                }
                self.assertIn("usuario_id", columns)
                _ensure_stock_user_column(connection)
        finally:
            engine.dispose()

    def test_configured_margin_is_enforced_and_price_report_works(self):
        product = self._create_product()
        admin_headers = self._headers(self.admin)
        changed = self.client.put(
            "/api/configuracoes",
            json={"margem_minima": 50, "limiar_giro": 8, "dias_validade": 10},
            headers=admin_headers,
        )
        self.assertEqual(changed.status_code, 200, changed.get_json())
        suggestion = self.client.post(
            "/api/sugestoes",
            json={"id_produto": product["id_produto"]},
            headers=self._headers(self.manager),
        )
        self.assertEqual(suggestion.status_code, 201, suggestion.get_json())
        self.assertEqual(suggestion.get_json()["preco_sugerido"], 19)
        decision = self.client.patch(
            f"/api/sugestoes/{suggestion.get_json()['id_sugestao']}",
            json={"decisao": "EDITADA", "preco": 14},
            headers=self._headers(self.manager),
        )
        self.assertEqual(decision.status_code, 400)

        sale = self.client.post(
            "/api/vendas",
            json={"id_produto": product["id_produto"], "quantidade": 2},
            headers=self._headers(self.manager),
        )
        self.assertEqual(sale.status_code, 201, sale.get_json())
        report = self.client.get(
            "/api/relatorios?tipo=vendas&inicio=2020-01-01"
            f"&fim={datetime.now().date().isoformat()}",
            headers=self._headers(self.manager),
        )
        self.assertEqual(report.status_code, 200, report.get_json())
        self.assertEqual(report.get_json()["dados"][0]["faturamento"], 40)

    def test_catalog_suggestions_for_500_products_meet_five_second_target(self):
        db.session.add_all(
            [
                Produto(
                    nome=f"Produto {index}",
                    codigo=f"P-{index}",
                    custo=10,
                    preco_atual=20,
                    estoque=10,
                    ativo=True,
                )
                for index in range(500)
            ]
        )
        db.session.commit()
        started = time.monotonic()
        response = self.client.post(
            "/api/sugestoes/lote",
            headers=self._headers(self.manager),
        )
        elapsed = time.monotonic() - started
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(len(response.get_json()), 500)
        self.assertLess(elapsed, 5, f"Geração demorou {elapsed:.2f} segundos")

    def test_catalog_turnover_reports_rolling_seven_and_thirty_days(self):
        product = self._create_product()
        now = datetime.utcnow()
        db.session.add_all(
            [
                Venda(
                    id_produto=product["id_produto"],
                    quantidade=3,
                    preco_unitario=20,
                    data_venda=now - timedelta(days=2),
                ),
                Venda(
                    id_produto=product["id_produto"],
                    quantidade=4,
                    preco_unitario=20,
                    data_venda=now - timedelta(days=10),
                ),
                Venda(
                    id_produto=product["id_produto"],
                    quantidade=5,
                    preco_unitario=20,
                    data_venda=now - timedelta(days=31),
                ),
                Venda(
                    id_produto=product["id_produto"],
                    quantidade=100,
                    preco_unitario=20,
                    data_venda=now + timedelta(days=1),
                ),
            ]
        )
        db.session.commit()

        response = self.client.get("/api/giro", headers=self._headers(self.common))

        self.assertEqual(response.status_code, 200, response.get_json())
        giro = next(
            item
            for item in response.get_json()
            if item["id_produto"] == product["id_produto"]
        )
        self.assertEqual(giro["quantidade_vendida_7_dias"], 3)
        self.assertEqual(giro["quantidade_vendida_30_dias"], 7)

    def test_expiration_discount_uses_strict_configured_day_limit(self):
        configuracao = db.session.get(ConfiguracaoRegras, 1)
        configuracao.limiar_giro = 0
        service = PrecificacaoAppService()
        today = date.today()

        def suggest(days_to_expiration):
            product = Produto(
                nome=f"Validade {days_to_expiration}",
                custo=10,
                preco_atual=20,
                estoque=5,
                ativo=True,
                data_validade=today + timedelta(days=days_to_expiration),
            )
            return service._montar_sugestao(
                product,
                Decimal("0"),
                None,
                self.manager.id,
                persistir=False,
                configuracao=configuracao,
            )

        self.assertEqual(suggest(6).preco_sugerido, Decimal("18.00"))
        self.assertEqual(suggest(7).preco_sugerido, Decimal("20.00"))
        self.assertEqual(suggest(-1).preco_sugerido, Decimal("20.00"))

    def test_high_turnover_increases_price_only_when_competitor_is_higher(self):
        configuracao = db.session.get(ConfiguracaoRegras, 1)
        service = PrecificacaoAppService()
        product = Produto(
            nome="Produto competitivo",
            custo=10,
            preco_atual=20,
            estoque=5,
            ativo=True,
        )

        suggested_with_competitor = service._montar_sugestao(
            product,
            Decimal("20"),
            Decimal("25"),
            self.manager.id,
            persistir=False,
            configuracao=configuracao,
        )
        suggested_without_competitor = service._montar_sugestao(
            product,
            Decimal("20"),
            None,
            self.manager.id,
            persistir=False,
            configuracao=configuracao,
        )

        self.assertEqual(
            suggested_with_competitor.preco_sugerido, Decimal("20.40")
        )
        self.assertEqual(
            suggested_without_competitor.preco_sugerido, Decimal("20.00")
        )

    def test_password_reset_uses_signed_token(self):
        from app.controllers.auth_controller import AuthController

        token = AuthController._serializer().dumps(self.manager.email)
        response = self.client.post(
            "/api/auth/redefinir-senha",
            json={"token": token, "nova_senha": "NewStrongPass123"},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(
            UsuarioService.autenticar("manager", "NewStrongPass123")[1], None
        )

    def test_health_endpoint_reports_database_state(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
