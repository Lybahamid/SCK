# fix_both.py — run once then delete
import os

# ══════════════════════════════════════════════════════════════════
# FILE 1: app/config.py  (Settings only, zero app imports)
# ══════════════════════════════════════════════════════════════════
config_content = """\
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SCK - Session Context Keeper"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "sck_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
"""

# ══════════════════════════════════════════════════════════════════
# FILE 2: migrations/env.py  (Alembic runner only)
# ══════════════════════════════════════════════════════════════════
env_content = """\
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# Resolve project root so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.database import Base
from app.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

# ══════════════════════════════════════════════════════════════════
# WRITE BOTH FILES
# ══════════════════════════════════════════════════════════════════
os.makedirs("app", exist_ok=True)
os.makedirs("migrations", exist_ok=True)

with open("app/config.py", "w", encoding="utf-8") as f:
    f.write(config_content)
print("OK  app/config.py written")

with open("migrations/env.py", "w", encoding="utf-8") as f:
    f.write(env_content)
print("OK  migrations/env.py written")

print("\nBoth files written successfully.")