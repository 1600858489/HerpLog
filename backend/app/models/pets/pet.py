from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IDMixin, SoftDeleteMixin, TimestampMixin
from .enums import PetSex


class Pet(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Represent one user's individually trackable pet."""

    __tablename__ = "pets"
    __table_args__ = (UniqueConstraint("user_id", "pet_code"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("personal_species.id"), nullable=False)
    pet_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    sex: Mapped[PetSex] = mapped_column(String(32), default=PetSex.UNKNOWN, nullable=False)
    identification_note: Mapped[str | None] = mapped_column(String(1000))
    owner_note: Mapped[str | None] = mapped_column(String(1000))

    species: Mapped["PersonalSpecies"] = relationship(lazy="raise")
    genes: Mapped[list["PersonalGene"]] = relationship(secondary="pet_genes", lazy="raise")
    identification_tags: Mapped[list["IdentificationTag"]] = relationship(
        secondary="pet_identification_tags", lazy="raise"
    )
    assignments: Mapped[list["PetManagementAssignment"]] = relationship(
        back_populates="pet", lazy="raise"
    )
    life_stages: Mapped[list["PetLifeStage"]] = relationship(
        back_populates="pet", lazy="raise"
    )
    origins: Mapped[list["PetOrigin"]] = relationship(
        back_populates="pet", foreign_keys="PetOrigin.pet_id", lazy="raise"
    )
