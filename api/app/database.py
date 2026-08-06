from collections.abc import AsyncGenerator
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings


def build_database_url():
    """Convert the Neon URL into the format required by SQLAlchemy asyncpg."""
    url = make_url(settings.database_url)

    # Neon normally supplies postgresql://, while asyncpg needs this driver.
    url = url.set(drivername="postgresql+asyncpg")

    # asyncpg receives SSL settings separately below.
    url = url.difference_update_query({"sslmode", "channel_binding"})

    return url


database_url = build_database_url()

connect_args: dict[str, object] = {
    "ssl": "require",
    "server_settings": {
        "jit": "off",
    },
}

engine_options: dict[str, object] = {
    "pool_pre_ping": True,
    "connect_args": connect_args,
}

# Neon pooled hostnames normally contain "-pooler".
# PgBouncer connections should not use SQLAlchemy's normal connection pool.
if database_url.host and "-pooler." in database_url.host:
    engine_options["poolclass"] = NullPool
    connect_args["prepared_statement_name_func"] = (
        lambda: f"__asyncpg_{uuid4()}__"
    )

engine = create_async_engine(
    database_url,
    **engine_options,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide one database session for a FastAPI request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """Run a small query to confirm that Neon is reachable."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return True