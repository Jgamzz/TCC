import os
from pathlib import Path

from sqlalchemy.engine import URL


def _load_local_env() -> None:
    """Load local development settings without overriding non-empty environment values."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
            value = value[1:-1]
        if key and not os.environ.get(key):
            os.environ[key] = value


_load_local_env()


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    PLANILHAS_CONCORRENTES_DIR = BASE_DIR / "database" / "concorrentes"

    # Configure as credenciais do MySQL por variáveis de ambiente.
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "sgb_varejo")

    SQLALCHEMY_DATABASE_URI = URL.create(
        "mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        query={"charset": "utf8mb4"},
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    PASSWORD_RESET_SALT = "sgb-varejo-password-reset"
    PASSWORD_RESET_MAX_AGE_SECONDS = 900
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM")
    APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "http://localhost:5000")
