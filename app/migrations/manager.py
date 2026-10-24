"""Sincroniza o banco com as tabelas declaradas no SQLAlchemy."""

from __future__ import annotations

import os
from typing import Any

from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    SmallInteger,
    String,
    create_engine,
    inspect,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.engine import URL
from werkzeug.security import generate_password_hash

from app import db
from app.models.cargo import Cargo
from app.models.configuracao_regras import ConfiguracaoRegras
from app.models.usuario import Usuario


def _create_database_if_needed(app: Any) -> None:
    """Cria o database MySQL antes de o SQLAlchemy abrir a conexão principal."""
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not str(uri).startswith("mysql"):
        return

    if not app.config.get("DB_PASSWORD"):
        raise RuntimeError(
            "DB_PASSWORD não está definida. Configure a senha do MySQL "
            "no ambiente antes de iniciar a aplicação."
        )

    server_url = URL.create(
        drivername="mysql+pymysql",
        username=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        host=app.config["DB_HOST"],
        port=int(app.config["DB_PORT"]),
        query={"charset": "utf8mb4"},
    )
    engine = create_engine(server_url)
    try:
        with engine.begin() as connection:
            database_name = app.config["DB_NAME"].replace("`", "``")
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        engine.dispose()


def _include_object(
    object_: Any,
    name: str,
    object_type: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """Não remove objetos existentes que não estejam descritos pelo ORM."""
    if object_type == "table" and reflected and compare_to is None:
        return False
    if object_type == "column" and reflected and compare_to is None:
        return False
    return True


def _ensure_user_auth_columns(connection: Any) -> None:
    """Adiciona colunas de autenticação ausentes em tabelas Usuario legadas."""
    tables = {name.lower(): name for name in inspect(connection).get_table_names()}
    table_name = tables.get(Usuario.__tablename__.lower())
    if table_name is None:
        return

    existing_columns = {
        column["name"].lower()
        for column in inspect(connection).get_columns(table_name)
    }
    additions = (
        Column("Email", String(254), nullable=True),
        Column(
            "failed_login_attempts",
            SmallInteger,
            nullable=False,
            server_default="0",
        ),
        Column("locked_until", DateTime, nullable=True),
        Column("password_reset_requested_at", DateTime, nullable=True),
    )
    operations = Operations(MigrationContext.configure(connection))
    for column in additions:
        if column.name.lower() not in existing_columns:
            operations.add_column(table_name, column)


def _ensure_stock_user_column(connection: Any) -> None:
    """Adiciona o responsável por movimentações em tabelas Estoque legadas."""
    tables = {name.lower(): name for name in inspect(connection).get_table_names()}
    table_name = tables.get("estoque")
    if table_name is None:
        return

    existing_columns = {
        column["name"].lower()
        for column in inspect(connection).get_columns(table_name)
    }
    if "usuario_id" not in existing_columns:
        operations = Operations(MigrationContext.configure(connection))
        operations.add_column(
            table_name,
            Column("usuario_id", Integer, nullable=True),
        )


def _apply_operations(
    operations: Operations,
    operation_list: list[Any],
    existing_tables: set[str],
    existing_indexes: dict[str, set[str]],
) -> None:
    """Aplica operações geradas, incluindo as agrupadas por tabela."""
    for operation in operation_list:
        nested_operations = getattr(operation, "ops", None)
        if nested_operations is not None:
            _apply_operations(
                operations, nested_operations, existing_tables, existing_indexes
            )
        elif (
            operation.__class__.__name__ == "CreateTableOp"
            and operation.table_name.lower() in existing_tables
        ):
            # MySQL costuma retornar nomes em minúsculas, embora o ORM preserve
            # a capitalização de tabelas legadas como "Cargo" e "Usuario".
            continue
        elif (
            operation.__class__.__name__ == "CreateIndexOp"
            and operation.index_name.lower()
            in existing_indexes.get(operation.table_name.lower(), set())
        ):
            continue
        else:
            operations.invoke(operation)


def _get_existing_indexes(connection: Any) -> dict[str, set[str]]:
    """Obtém índices existentes para evitar criações duplicadas no MySQL."""
    inspector = inspect(connection)
    indexes: dict[str, set[str]] = {}
    for table_name in inspector.get_table_names():
        indexes[table_name.lower()] = {
            index["name"].lower()
            for index in inspector.get_indexes(table_name)
            if index.get("name")
        }
    return indexes


def _rename_roles(connection: Any) -> None:
    """Atualiza os nomes legados dos cargos sem alterar seus IDs."""
    connection.execute(
        text(
            "UPDATE Cargo SET Name = :new_name "
            "WHERE UPPER(Name) = :old_name"
        ),
        {"new_name": "Admin", "old_name": "DONO"},
    )
    connection.execute(
        text(
            "UPDATE Cargo SET Name = :new_name "
            "WHERE UPPER(Name) = :old_name"
        ),
        {"new_name": "Usu\u00e1rio", "old_name": "FUNCIONARIO"},
    )


def _seed_default_roles(connection: Any) -> None:
    """Garante os cargos usados pelas permissões padrão da aplicação."""
    table = Cargo.__table__
    roles = (
        (1, "Admin"),
        (2, "Gerente"),
        (3, "Usu\u00e1rio"),
    )
    for role_id, name in roles:
        role = connection.execute(
            select(table.c["ID"]).where(table.c["ID"] == role_id)
        ).first()
        if role is None:
            connection.execute(
                insert(table).values(
                    ID=role_id,
                    Name=name,
                    Is_Active=True,
                )
            )
        else:
            connection.execute(
                update(table)
                .where(table.c["ID"] == role_id)
                .values(Name=name, Is_Active=True)
            )


def _migrate_legacy_passwords(connection: Any) -> None:
    """Converte senhas legadas em texto puro para hashes com salt."""
    table = Usuario.__table__
    password_column = table.c["Password"]
    rows = connection.execute(select(table.c["ID"], password_column)).all()
    for user_id, password in rows:
        if password and not password.startswith(("pbkdf2:", "scrypt:")):
            connection.execute(
                update(table)
                .where(table.c["ID"] == user_id)
                .values(Password=generate_password_hash(password, method="scrypt"))
            )


def _seed_initial_admin(connection: Any) -> None:
    """Cria o primeiro administrador somente com credenciais fornecidas no ambiente."""
    username = os.getenv("INITIAL_ADMIN_USERNAME")
    password = os.getenv("INITIAL_ADMIN_PASSWORD")
    name = os.getenv("INITIAL_ADMIN_NAME")
    if not username or not password or not name:
        return
    table = Usuario.__table__
    exists = connection.execute(
        select(table.c["ID"]).where(table.c["Cargo_ID"] == 1)
    ).first()
    if exists:
        return
    connection.execute(
        insert(table).values(
            Name=name.strip(),
            Username=username.strip(),
            Password=generate_password_hash(password, method="scrypt"),
            Is_Active=True,
            Cargo_ID=1,
        )
    )


def _seed_default_configuration(connection: Any) -> None:
    table = ConfiguracaoRegras.__table__
    if connection.execute(select(table.c.id_configuracao).limit(1)).first():
        return
    connection.execute(
        insert(table).values(
            id_configuracao=1,
            limiar_giro=10,
            dias_validade=7,
            margem_minima=15,
        )
    )


def migrate_database(app: Any) -> None:
    """Cria tabelas novas e atualiza colunas conforme o metadata do ORM."""
    _create_database_if_needed(app)

    # create_all cobre o primeiro bootstrap e deixa o autogerador focado em updates.
    db.create_all()

    with db.engine.begin() as connection:
        _ensure_user_auth_columns(connection)
        _ensure_stock_user_column(connection)
        context = MigrationContext.configure(
            connection,
            opts={
                "compare_type": True,
                "include_object": _include_object,
            },
        )
        migration = produce_migrations(context, db.metadata)
        if not migration.upgrade_ops.is_empty():
            existing_tables = {
                table_name.lower() for table_name in inspect(connection).get_table_names()
            }
            existing_indexes = _get_existing_indexes(connection)
            _apply_operations(
                Operations(context),
                migration.upgrade_ops.ops,
                existing_tables,
                existing_indexes,
            )
        _seed_default_roles(connection)
        _rename_roles(connection)
        _migrate_legacy_passwords(connection)
        _seed_initial_admin(connection)
        _seed_default_configuration(connection)
