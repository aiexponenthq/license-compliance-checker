# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Database session management.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from lcc.config import LCCConfig, load_config


def resolve_database_url(config: LCCConfig) -> str:
    """Build the async SQLAlchemy URL for a given config.

    Use PostgreSQL if configured, otherwise fall back to SQLite (for dev/tests).
    Note: SQLite with asyncio requires the aiosqlite driver.
    """
    return config.database_url or f"sqlite+aiosqlite:///{config.database_path}"


config = load_config()

DATABASE_URL = resolve_database_url(config)

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


def configure_engine(database_url: str | None = None, echo: bool = False) -> None:
    """(Re)create the module-level async engine and session factory.

    Allows the application to bind to the database selected by the active
    configuration (e.g. LCC_DB_PATH / LCC_DATABASE_URL) at startup, rather than
    only the value that was present when this module was first imported.
    """
    global engine, AsyncSessionLocal, DATABASE_URL

    if database_url is None:
        database_url = resolve_database_url(load_config())

    DATABASE_URL = database_url
    engine = create_async_engine(database_url, echo=echo, future=True)
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def init_models() -> None:
    """Create the SQLAlchemy schema (tables) for the current engine if missing."""
    # Imported here to avoid a circular import at module load time.
    from lcc.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
