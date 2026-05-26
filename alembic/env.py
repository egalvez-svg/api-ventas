from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

# Import all models so their metadata is registered
import app.models.base       # noqa: F401
import app.models.inventory  # noqa: F401
import app.models.sales      # noqa: F401

from app.core.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use SQLModel metadata (which wraps SQLAlchemy metadata)
target_metadata = SQLModel.metadata

# Alembic uses a sync driver — strip +asyncpg so psycopg2 is used instead
_db_url = get_settings().DATABASE_URL.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", _db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import inspect, text

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Pre-flight check: stamp new deployments where tables exist but Alembic has
    # no version yet. Use a dedicated connection so the transaction is fully
    # committed before we hand a clean connection to Alembic.
    with connectable.connect() as pre_conn:
        inspector = inspect(pre_conn)
        has_alembic = inspector.has_table("alembic_version")
        has_version = False
        if has_alembic:
            try:
                res = pre_conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                has_version = bool(res and res[0])
            except Exception:
                pass

        if not has_version and inspector.has_table("branch"):
            from alembic.script import ScriptDirectory
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_current_head()
            if head_rev:
                print(f"[alembic/env.py] Existing tables detected without Alembic version. Stamping to head: {head_rev}")
                if not has_alembic:
                    pre_conn.execute(text(
                        "CREATE TABLE alembic_version ("
                        "version_num VARCHAR(32) NOT NULL, "
                        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
                        ")"
                    ))
                pre_conn.execute(text("DELETE FROM alembic_version"))
                pre_conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
                    {"version": head_rev},
                )
                pre_conn.commit()

    # Migration connection: fresh, no open transaction.
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
