from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IDMixin, SoftDeleteMixin, TimestampMixin, UTCDateTime


class ManagementUnitType(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Store a system or user-defined flat management-unit type."""

    __tablename__ = "management_unit_types"
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ManagementUnit(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Represent one flat physical environment used for batch management."""

    __tablename__ = "management_units"
    __table_args__ = (UniqueConstraint("user_id", "unit_code"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("management_unit_types.id"), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(1000))

    unit_type: Mapped["ManagementUnitType"] = relationship(lazy="raise")
    assignments: Mapped[list["PetManagementAssignment"]] = relationship(
        back_populates="management_unit", lazy="raise"
    )


class PetManagementAssignment(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Record one historical assignment of a pet to a management unit."""

    __tablename__ = "pet_management_assignments"

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False, index=True)
    management_unit_id: Mapped[int] = mapped_column(
        ForeignKey("management_units.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    life_stage: Mapped[str | None] = mapped_column(String(255))
    transfer_reason: Mapped[str | None] = mapped_column(String(1000))
    note: Mapped[str | None] = mapped_column(String(1000))

    pet: Mapped["Pet"] = relationship(back_populates="assignments", lazy="raise")
    management_unit: Mapped[ManagementUnit] = relationship(
        back_populates="assignments", lazy="raise"
    )
