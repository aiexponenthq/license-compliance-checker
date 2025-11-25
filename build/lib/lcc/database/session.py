"""
Database session management.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from lcc.config import load_config

config = load_config()

# Use PostgreSQL if configured, otherwise fallback to SQLite (for dev/tests)
# Note: SQLite with asyncio requires aiosqlite driver
DATABASE_URL = config.database_url or f"sqlite+aiosqlite:///{config.database_path}"

engine = create_async_engine(
    DATABASE_URL,
    echo=config.log_level == "DEBUG",
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
