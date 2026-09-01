from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, IDMixin, SoftDeleteMixin, TimestampMixin
from .enums import InheritanceMode


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
