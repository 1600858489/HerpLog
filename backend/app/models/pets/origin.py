from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IDMixin, SoftDeleteMixin, TimestampMixin, UTCDateTime
from .enums import ConfidenceLevel, PetOriginType, PetParentRole


class PetOrigin(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Record one source, parent claim, or external breeding detail."""

    __tablename__ = "pet_origins"

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False, index=True)
    origin_type: Mapped[PetOriginType] = mapped_column(String(32), nullable=False)
    parent_role: Mapped[PetParentRole] = mapped_column(
        String(32), default=PetParentRole.UNSPECIFIED, nullable=False
    )
    parent_pet_id: Mapped[int | None] = mapped_column(ForeignKey("pets.id"), nullable=True)
    breeder_name: Mapped[str | None] = mapped_column(String(255))
    external_name: Mapped[str | None] = mapped_column(String(255))
    genetic_note: Mapped[str | None] = mapped_column(String(1000))
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        String(32), default=ConfidenceLevel.UNKNOWN, nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(1000))

    pet: Mapped["Pet"] = relationship(
        back_populates="origins", foreign_keys=[pet_id], lazy="raise"
    )
    parent_pet: Mapped["Pet | None"] = relationship(foreign_keys=[parent_pet_id], lazy="raise")
