from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IDMixin, SoftDeleteMixin, TimestampMixin, UTCDateTime

if TYPE_CHECKING:
    from .user import User


class PetSex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class PetOriginType(StrEnum):
    SELF_BRED = "self_bred"
    BREEDER = "breeder"
    PURCHASED = "purchased"
    UNKNOWN = "unknown"


class PetParentRole(StrEnum):
    SIRE = "sire"
    DAM = "dam"
    UNSPECIFIED = "unspecified"


class ConfidenceLevel(StrEnum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    UNKNOWN = "unknown"


class InheritanceMode(StrEnum):
    DOMINANT = "dominant"
    RECESSIVE = "recessive"
    INCOMPLETE_DOMINANT = "incomplete_dominant"
    CODOMINANT = "codominant"
    UNKNOWN = "unknown"


class PersonalSpecies(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Store one user's reusable species and optional scientific taxonomy."""

    __tablename__ = "personal_species"
    __table_args__ = (UniqueConstraint("user_id", "common_name"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scientific_name: Mapped[str | None] = mapped_column(String(255))
    kingdom: Mapped[str | None] = mapped_column(String(255))
    phylum: Mapped[str | None] = mapped_column(String(255))
    class_name: Mapped[str | None] = mapped_column(String(255))
    order_name: Mapped[str | None] = mapped_column(String(255))
    family: Mapped[str | None] = mapped_column(String(255))
    genus: Mapped[str | None] = mapped_column(String(255))
    species_name: Mapped[str | None] = mapped_column(String(255))
    subspecies: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(1000))


class PersonalGene(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Store one user's reusable gene or morph option."""

    __tablename__ = "personal_genes"
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phenotype: Mapped[str | None] = mapped_column(String(255))
    genotype: Mapped[str | None] = mapped_column(String(255))
    inheritance_mode: Mapped[InheritanceMode | None] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(String(1000))


class IdentificationTag(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Store one user's reusable physical-identification tag."""

    __tablename__ = "identification_tags"
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


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

    unit_type: Mapped[ManagementUnitType] = relationship(lazy="raise")
    assignments: Mapped[list[PetManagementAssignment]] = relationship(lazy="raise")


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

    species: Mapped[PersonalSpecies] = relationship(lazy="raise")
    genes: Mapped[list[PersonalGene]] = relationship(secondary="pet_genes", lazy="raise")
    identification_tags: Mapped[list[IdentificationTag]] = relationship(
        secondary="pet_identification_tags", lazy="raise"
    )
    assignments: Mapped[list[PetManagementAssignment]] = relationship(lazy="raise")
    life_stages: Mapped[list[PetLifeStage]] = relationship(lazy="raise")
    origins: Mapped[list[PetOrigin]] = relationship(
        foreign_keys="PetOrigin.pet_id", lazy="raise"
    )


class PetGene(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Store one pet-to-gene association with lifecycle metadata."""

    __tablename__ = "pet_genes"
    __table_args__ = (UniqueConstraint("pet_id", "gene_id"),)

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    gene_id: Mapped[int] = mapped_column(ForeignKey("personal_genes.id"), nullable=False)


class PetIdentificationTag(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Store one pet-to-identification-tag association."""

    __tablename__ = "pet_identification_tags"
    __table_args__ = (UniqueConstraint("pet_id", "tag_id"),)

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("identification_tags.id"), nullable=False)


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

    pet: Mapped[Pet] = relationship(back_populates="assignments", lazy="raise")
    management_unit: Mapped[ManagementUnit] = relationship(
        back_populates="assignments", lazy="raise"
    )


class PetLifeStage(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Record one historical life-stage interval for a pet."""

    __tablename__ = "pet_life_stages"

    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    change_reason: Mapped[str | None] = mapped_column(String(1000))
    note: Mapped[str | None] = mapped_column(String(1000))

    pet: Mapped[Pet] = relationship(back_populates="life_stages", lazy="raise")


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

    pet: Mapped[Pet] = relationship(
        back_populates="origins", foreign_keys=[pet_id], lazy="raise"
    )
    parent_pet: Mapped[Pet | None] = relationship(foreign_keys=[parent_pet_id], lazy="raise")
