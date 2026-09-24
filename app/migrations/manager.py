"""Sincroniza o banco com as tabelas declaradas no SQLAlchemy."""

from __future__ import annotations

from typing import Any

from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, insert, select, text, update
from sqlalchemy.engine import URL

from app import db
from app.models.cargo import Cargo
from app.models.usuario import Usuario


def _create_database_if_needed(app: Any) -> None:
    """Cria o database MySQL antes de o SQLAlchemy abrir a conexão principal."""
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("mysql"):
        return

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


def _apply_operations(
    operations: Operations, operation_list: list[Any], existing_tables: set[str]
) -> None:
    """Aplica operações geradas, incluindo as agrupadas por tabela."""
    for operation in operation_list:
        nested_operations = getattr(operation, "ops", None)
        if nested_operations is not None:
            _apply_operations(operations, nested_operations, existing_tables)
        elif (
            operation.__class__.__name__ == "CreateTableOp"
            and operation.table_name.lower() in existing_tables
        ):
            # MySQL costuma retornar nomes em minúsculas, embora o ORM preserve
            # a capitalização de tabelas legadas como "Cargo" e "Usuario".
            continue
        else:
            operations.invoke(operation)


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


def _seed_default_users(connection: Any) -> None:
    """Insere os usuários iniciais somente quando ID e username ainda não existem."""
    users = (
        {
            "id": 1,
            "name": "Kau\u00e3",
            "username": "Kau\u00e3",
            "password": "Senha123",
            "cargo_id": 3,
        },
        {
            "id": 2,
            "name": "Tanaka",
            "username": "Tanaka",
            "password": "Senha123",
            "cargo_id": 2,
        },
        {
            "id": 3,
            "name": "Bernardo",
            "username": "Bernardo",
            "password": "Senha123",
            "cargo_id": 1,
        },
    )
    table = Usuario.__table__
    id_column = table.c["ID"]
    username_column = table.c["Username"]

    for user in users:
        existing = connection.execute(
            select(id_column).where(
                (id_column == user["id"]) | (username_column == user["username"])
            )
        ).first()
        if existing is None:
            connection.execute(
                insert(table).values(
                    ID=user["id"],
                    Name=user["name"],
                    Username=user["username"],
                    Password=user["password"],
                    Is_Active=True,
                    Cargo_ID=user["cargo_id"],
                )
            )
        else:
            connection.execute(
                update(table)
                .where(
                    (id_column == user["id"]) | (username_column == user["username"])
                )
                .values(
                    Password=user["password"],
                    Cargo_ID=user["cargo_id"],
                )
            )


def migrate_database(app: Any) -> None:
    """Cria tabelas novas e atualiza colunas conforme o metadata do ORM."""
    _create_database_if_needed(app)

    # create_all cobre o primeiro bootstrap e deixa o autogerador focado em updates.
    db.create_all()

    with db.engine.begin() as connection:
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
            _apply_operations(
                Operations(context), migration.upgrade_ops.ops, existing_tables
            )
        _seed_default_roles(connection)
        _rename_roles(connection)
        _seed_default_users(connection)
