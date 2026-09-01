from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from ..utils.datetime import utc_now
from ..utils.uuid import generate_uuid


class UUIDString(TypeDecorator[UUID]):
    """Store UUID values as portable strings across SQLite and PostgreSQL."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: UUID | str | None, dialect) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: str | None, dialect) -> UUID | None:
        return UUID(value) if value is not None else None


class UTCDateTime(TypeDecorator[datetime]):
    """Store UTC datetimes consistently and return timezone-aware values."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).replace(tzinfo=None)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class IDMixin:
    """Provide an internal integer key and a public UUID key."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(UUIDString(), unique=True, index=True, default=generate_uuid)


class TimestampMixin:
    """Provide UTC creation and update timestamps."""

    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now, nullable=False)


class SoftDeleteMixin:
    """Provide a nullable timestamp used for service-managed soft deletion."""

    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


__all__ = ["Base", "IDMixin", "TimestampMixin", "SoftDeleteMixin", "UTCDateTime"]
