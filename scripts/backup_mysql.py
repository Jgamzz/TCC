import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def backup_database():
    database = os.getenv("DB_NAME", "sgb_varejo")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    executable = os.getenv("MYSQLDUMP_BIN", "mysqldump")
    backup_dir = Path(os.getenv("DB_BACKUP_DIR", "backups")).resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"sgpv-{timestamp}.sql.gz"
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    command = [
        executable,
        "--single-transaction",
        "--routines",
        "--triggers",
        "--host",
        host,
        "--port",
        port,
        "--user",
        user,
        "--databases",
        database,
    ]
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = password

    try:
        with temporary.open("wb") as raw_file:
            with gzip.GzipFile(fileobj=raw_file, mode="wb") as compressed:
                result = subprocess.run(
                    command,
                    stdout=compressed,
                    stderr=subprocess.PIPE,
                    env=environment,
                    check=False,
                    timeout=7200,
                )
        if result.returncode != 0:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"mysqldump falhou (código {result.returncode}): {message}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    limite = datetime.now(timezone.utc) - timedelta(days=30)
    for arquivo in backup_dir.glob("sgpv-*.sql.gz"):
        modificado = datetime.fromtimestamp(arquivo.stat().st_mtime, timezone.utc)
        if modificado < limite:
            arquivo.unlink()
    return destination


if __name__ == "__main__":
    try:
        print(backup_database())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Falha no backup do banco: {error}", file=sys.stderr)
        raise SystemExit(1) from error
