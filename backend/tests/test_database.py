from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database import dispose_database, engine
from app.models.base import Base, IDMixin, SoftDeleteMixin, TimestampMixin


class ExampleRecord(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "example_records"

    name: Mapped[str] = mapped_column(String(100))


async def test_dispose_database_disposes_global_engine(monkeypatch) -> None:
    disposed = False

    async def fake_dispose() -> None:
        nonlocal disposed
        disposed = True

    import app.infra.database as database

    class FakeEngine:
        async def dispose(self) -> None:
            await fake_dispose()

    monkeypatch.setattr(database, "engine", FakeEngine())
    await dispose_database()
    assert disposed


async def test_global_engine_uses_configured_postgres_pool() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert engine.url.drivername == "postgresql+asyncpg"
    assert engine.pool.size() == settings.database_pool_size
    assert engine.pool._max_overflow == settings.database_max_overflow


async def test_public_mixins(async_session_factory) -> None:
    async with async_session_factory() as session:
        record = ExampleRecord(name="sample")
        session.add(record)
        await session.commit()
        await session.refresh(record)

        assert isinstance(record.id, int)
        assert isinstance(record.uuid, UUID)
        assert record.created_at.tzinfo is not None
        assert record.updated_at.tzinfo is not None
        assert record.deleted_at is None


async def test_database_is_postgres(async_session_factory) -> None:
    assert async_session_factory.kw["bind"].url.drivername == "postgresql+asyncpg"
