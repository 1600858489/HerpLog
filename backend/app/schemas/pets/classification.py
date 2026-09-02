from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..base import BaseRequestSchema


class SpeciesCreateRequest(BaseRequestSchema):
    """Validate a personal species with optional scientific taxonomy."""

    common_name: str = Field(min_length=1, max_length=255)
    scientific_name: str | None = Field(default=None, max_length=255)
    kingdom: str | None = Field(default=None, max_length=255)
    phylum: str | None = Field(default=None, max_length=255)
    class_name: str | None = Field(default=None, max_length=255)
    order_name: str | None = Field(default=None, max_length=255)
    family: str | None = Field(default=None, max_length=255)
    genus: str | None = Field(default=None, max_length=255)
    species_name: str | None = Field(default=None, max_length=255)
    subspecies: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator(
        "common_name", "scientific_name", "kingdom", "phylum", "class_name",
        "order_name", "family", "genus", "species_name", "subspecies", "note",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SpeciesUpdateRequest(SpeciesCreateRequest):
    """Validate editable species fields."""


class SpeciesResponse(BaseModel):
    """Serialize a personal species."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    common_name: str
    scientific_name: str | None
    kingdom: str | None
    phylum: str | None
    class_name: str | None
    order_name: str | None
    family: str | None
    genus: str | None
    species_name: str | None
    subspecies: str | None
    note: str | None


class GeneCreateRequest(BaseRequestSchema):
    """Validate a reusable personal gene option."""

    name: str = Field(min_length=1, max_length=255)
    phenotype: str | None = Field(default=None, max_length=255)
    genotype: str | None = Field(default=None, max_length=255)
    inheritance_mode: str | None = Field(default=None, max_length=32)
    note: str | None = Field(default=None, max_length=1000)


class GeneUpdateRequest(GeneCreateRequest):
    """Validate editable gene fields."""


class GeneResponse(BaseModel):
    """Serialize a reusable personal gene option."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    phenotype: str | None
    genotype: str | None
    inheritance_mode: str | None
    note: str | None


class TagCreateRequest(BaseRequestSchema):
    """Validate a reusable personal identification tag."""

    name: str = Field(min_length=1, max_length=255)


class TagUpdateRequest(TagCreateRequest):
    """Validate an editable identification tag."""


class TagResponse(BaseModel):
    """Serialize a personal identification tag."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str


class SpeciesSummary(BaseModel):
    """Serialize minimum species fields used by a pet list."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    common_name: str


class IdentificationTagSummary(BaseModel):
    """Serialize a compact identification tag."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str


__all__ = [
    "GeneCreateRequest", "GeneResponse", "GeneUpdateRequest",
    "IdentificationTagSummary", "SpeciesCreateRequest", "SpeciesResponse",
    "SpeciesSummary", "SpeciesUpdateRequest", "TagCreateRequest", "TagResponse",
    "TagUpdateRequest",
]
