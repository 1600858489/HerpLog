from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, IDMixin, SoftDeleteMixin, TimestampMixin


class ExampleRecord(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "example_records"

    name: Mapped[str] = mapped_column(String(100))


async def test_create_all_and_public_mixins(async_session_factory) -> None:
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
