"""
Pre-start migration script para Render.

Detecta si las tablas ya existen sin registro de Alembic
(creadas con create_all en deploys anteriores) y las sella
en la revisión actual antes de correr upgrade head.
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from alembic.config import Config
from alembic import command

CURRENT_HEAD = "f3c8a2e1b7d4"

DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


def get_alembic_version(conn) -> str | None:
    cur = conn.cursor()
    try:
        cur.execute("SELECT version_num FROM alembic_version LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        return None
    finally:
        cur.close()


def tables_exist(conn) -> bool:
    cur = conn.cursor()
    try:
        cur.execute("SELECT to_regclass('public.branch')")
        return cur.fetchone()[0] is not None
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()


def main() -> None:
    conn = psycopg2.connect(DATABASE_URL)
    cfg = Config("alembic.ini")

    try:
        version = get_alembic_version(conn)

        if version is None and tables_exist(conn):
            print(f"[prestart] Tablas existentes sin versión Alembic. Sellando en {CURRENT_HEAD}...")
            command.stamp(cfg, CURRENT_HEAD)
        elif version:
            print(f"[prestart] Versión Alembic actual: {version}")
        else:
            print("[prestart] Base de datos nueva — se aplicarán todas las migraciones.")
    finally:
        conn.close()

    print("[prestart] Ejecutando alembic upgrade head...")
    command.upgrade(cfg, "head")
    print("[prestart] Migraciones completadas.")


if __name__ == "__main__":
    main()
