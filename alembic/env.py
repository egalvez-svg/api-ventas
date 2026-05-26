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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Check if the tables exist but alembic_version doesn't have a version registered
        from sqlalchemy import inspect, text
        inspector = inspect(connection)
        
        has_alembic = inspector.has_table("alembic_version")
        has_version = False
        if has_alembic:
            try:
                res = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                if res and res[0]:
                    has_version = True
            except Exception:
                pass
                
        if not has_version and inspector.has_table("branch"):
            from alembic.script import ScriptDirectory
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_current_head()
            
            if head_rev:
                print(f"[alembic/env.py] Existing tables ('branch') detected without Alembic version. Stamping to head: {head_rev}")
                if not has_alembic:
                    connection.execute(text(
                        "CREATE TABLE alembic_version ("
                        "version_num VARCHAR(32) NOT NULL, "
                        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
                        ")"
                    ))
                connection.execute(text("DELETE FROM alembic_version"))
                connection.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
                    {"version": head_rev}
                )
                try:
                    connection.commit()
                except Exception:
                    pass

        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
