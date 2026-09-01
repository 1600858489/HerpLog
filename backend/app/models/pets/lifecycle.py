from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IDMixin, SoftDeleteMixin, TimestampMixin, UTCDateTime


class PetLifeStage(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Record one historical life-stage interval for a pet."""

    __tablename__ = "pet_life_stages"

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    change_reason: Mapped[str | None] = mapped_column(String(1000))
    note: Mapped[str | None] = mapped_column(String(1000))

    pet: Mapped["Pet"] = relationship(back_populates="life_stages", lazy="raise")
