from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import get_settings


settings = get_settings()
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped async session and close it afterward."""
    async with async_session_factory() as session:
        yield session


async def dispose_database() -> None:
    """Dispose the process-level PostgreSQL connection pool."""
    await engine.dispose()


__all__ = ["engine", "async_session_factory", "get_db_session", "dispose_database"]
