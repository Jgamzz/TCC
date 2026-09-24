"""Infraestrutura de criação e atualização automática do schema."""

from app.migrations.manager import migrate_database

__all__ = ["migrate_database"]
