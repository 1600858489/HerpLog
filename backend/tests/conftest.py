import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker, create_async_engine

from app.infra.database import get_db_session
from app.infra.redis import close_redis_client, create_redis_client
from main import app

# Application tables are owned by Alembic; tests only truncate their data.
APPLICATION_TABLES = [
    "pet_identification_tags",
    "pet_management_assignments",
    "pet_life_stages",
    "pet_origins",
    "pet_genes",
    "pets",
    "management_units",
    "management_unit_types",
    "personal_genes",
    "personal_species",
    "identification_tags",
    "refresh_tokens",
    "users",
]


def _test_database_url() -> str:
    """Resolve the isolated PostgreSQL test database URL."""
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("tests require TEST_DATABASE_URL or DATABASE_URL to point at PostgreSQL")
    if url.rstrip("/").endswith("herplog"):
        raise RuntimeError("tests must not run against the development database")
    return url


@pytest_asyncio.fixture(scope="session")
def database_url() -> str:
    return _test_database_url()


@pytest_asyncio.fixture
async def database_connection(database_url) -> AsyncConnection:
    """Yield a connection after ensuring the test schema exists and is empty."""
    engine = create_async_engine(database_url, pool_pre_ping=True)
    from app.models.base import Base

    example_table = Base.metadata.tables["example_records"]
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=[example_table])
        for table in APPLICATION_TABLES:
            await connection.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    yield engine
    async with engine.begin() as connection:
        # Test-only table must not linger or alembic check would see schema drift.
        await connection.run_sync(example_table.drop, checkfirst=True)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_factory(database_connection) -> async_sessionmaker[AsyncSession]:
    factory = async_sessionmaker(database_connection, expire_on_commit=False)
    yield factory


@pytest_asyncio.fixture
async def client(async_session_factory) -> AsyncClient:
    async def override_get_db_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def redis_client() -> Redis:
    client = create_redis_client()
    await client.ping()
    yield client
    await close_redis_client(client)


__all__ = ["async_session_factory", "client", "redis_client"]
