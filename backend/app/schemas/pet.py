from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import BaseRequestSchema


class PetResponseBase(BaseModel):
    """Serialize public pet fields without database ownership details."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID


class SpeciesCreateRequest(BaseRequestSchema):
    """Validate a user-owned species record."""

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
        "common_name",
        "scientific_name",
        "kingdom",
        "phylum",
        "class_name",
        "order_name",
        "family",
        "genus",
        "species_name",
        "subspecies",
        "note",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class SpeciesUpdateRequest(SpeciesCreateRequest):
    """Validate editable fields for one species record."""


class SpeciesResponse(PetResponseBase, SpeciesCreateRequest):
    """Serialize a user-owned species and optional scientific taxonomy."""


class GeneCreateRequest(BaseRequestSchema):
    """Validate a reusable personal gene option."""

    name: str = Field(min_length=1, max_length=255)
    phenotype: str | None = Field(default=None, max_length=255)
    genotype: str | None = Field(default=None, max_length=255)
    inheritance_mode: str | None = Field(default=None, max_length=32)
    note: str | None = Field(default=None, max_length=1000)


class GeneUpdateRequest(GeneCreateRequest):
    """Validate editable fields for one gene option."""


class GeneResponse(PetResponseBase, GeneCreateRequest):
    """Serialize a reusable personal gene option."""


class TagCreateRequest(BaseRequestSchema):
    """Validate a reusable personal identification tag."""

    name: str = Field(min_length=1, max_length=255)


class TagUpdateRequest(TagCreateRequest):
    """Validate an editable identification tag."""


class TagResponse(PetResponseBase, TagCreateRequest):
    """Serialize a personal identification tag."""


class ManagementUnitTypeCreateRequest(BaseRequestSchema):
    """Validate a user-defined management unit type."""

    name: str = Field(min_length=1, max_length=255)


class ManagementUnitTypeUpdateRequest(ManagementUnitTypeCreateRequest):
    """Validate an editable management unit type."""


class ManagementUnitTypeResponse(PetResponseBase, ManagementUnitTypeCreateRequest):
    """Serialize a management unit type."""

    is_system: bool


class ManagementUnitCreateRequest(BaseRequestSchema):
    """Validate a flat management unit creation request."""

    type_uuid: UUID
    unit_code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=1000)


class ManagementUnitUpdateRequest(BaseRequestSchema):
    """Validate editable management unit fields."""

    unit_code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=1000)


class ManagementUnitResponse(PetResponseBase, ManagementUnitUpdateRequest):
    """Serialize a flat management unit."""

    unit_code: str
    type: ManagementUnitTypeResponse


class PetCreateRequest(BaseRequestSchema):
    """Validate creation of a pet identified by a personal species."""

    species_uuid: UUID
    sex: str = "unknown"
    name: str | None = Field(default=None, max_length=255)
    pet_code: str | None = Field(default=None, max_length=64)
    identification_note: str | None = Field(default=None, max_length=1000)
    owner_note: str | None = Field(default=None, max_length=1000)
    gene_uuids: list[UUID] = Field(default_factory=list)
    tag_uuids: list[UUID] = Field(default_factory=list)


class PetUpdateRequest(BaseRequestSchema):
    """Validate editable pet base fields."""

    species_uuid: UUID | None = None
    sex: str | None = None
    name: str | None = Field(default=None, max_length=255)
    pet_code: str | None = Field(default=None, max_length=64)
    identification_note: str | None = Field(default=None, max_length=1000)
    owner_note: str | None = Field(default=None, max_length=1000)


class SpeciesSummary(PetResponseBase):
    """Serialize the minimum species fields used in pet lists."""

    common_name: str


class IdentificationTagSummary(PetResponseBase):
    """Serialize one identification tag in a pet list."""

    name: str


class ManagementUnitSummary(PetResponseBase):
    """Serialize the current management unit in a pet list."""

    name: str | None
    unit_code: str


class PetListResponse(PetResponseBase):
    """Serialize the compact pet list representation."""

    pet_code: str
    name: str | None
    species: SpeciesSummary
    sex: str
    current_management_unit: ManagementUnitSummary | None
    identification_tags: list[IdentificationTagSummary]


class PetResponse(PetListResponse):
    """Serialize a pet detail representation."""

    identification_note: str | None
    owner_note: str | None
    genes: list[GeneResponse]
    origins: list[OriginResponse]
    life_stages: list[LifeStageResponse]
    management_assignments: list[AssignmentResponse]


class PetListFilters(BaseModel):
    """Represent validated pet list filters for Selector queries."""

    species_uuid: UUID | None = None
    sex: str | None = None
    management_unit_uuid: UUID | None = None
    assigned: bool | None = None
    tag_uuid: UUID | None = None
    keyword: str | None = None


class AssignmentCreateRequest(BaseRequestSchema):
    """Validate adding a pet to a management unit."""

    management_unit_uuid: UUID
    started_at: datetime
    life_stage: str | None = None
    transfer_reason: str | None = None
    note: str | None = None


class AssignmentMoveRequest(AssignmentCreateRequest):
    """Validate moving a pet to another management unit."""


class AssignmentResponse(PetResponseBase):
    """Serialize one historical management assignment."""

    management_unit: ManagementUnitSummary
    started_at: datetime
    ended_at: datetime | None
    life_stage: str | None
    transfer_reason: str | None
    note: str | None


class LifeStageCreateRequest(BaseRequestSchema):
    """Validate creation of a pet life-stage interval."""

    stage: str = Field(min_length=1, max_length=255)
    started_at: datetime
    change_reason: str | None = None
    note: str | None = None


class LifeStageUpdateRequest(BaseRequestSchema):
    """Validate editable life-stage fields."""

    stage: str | None = Field(default=None, max_length=255)
    change_reason: str | None = None
    note: str | None = None


class LifeStageResponse(PetResponseBase):
    """Serialize one historical life-stage interval."""

    stage: str
    started_at: datetime
    ended_at: datetime | None
    change_reason: str | None
    note: str | None


class OriginCreateRequest(BaseRequestSchema):
    """Validate one source or parent claim for a pet."""

    origin_type: str
    parent_role: str = "unspecified"
    parent_pet_uuid: UUID | None = None
    breeder_name: str | None = None
    external_name: str | None = None
    genetic_note: str | None = None
    confidence: str = "unknown"
    note: str | None = None


class OriginUpdateRequest(OriginCreateRequest):
    """Validate editable source or parent claim fields."""


class OriginResponse(PetResponseBase):
    """Serialize one source or parent claim."""

    origin_type: str
    parent_role: str
    parent_pet_uuid: UUID | None
    breeder_name: str | None
    external_name: str | None
    genetic_note: str | None
    confidence: str
    note: str | None


__all__ = [
    "AssignmentCreateRequest",
    "AssignmentMoveRequest",
    "AssignmentResponse",
    "GeneCreateRequest",
    "GeneResponse",
    "GeneUpdateRequest",
    "IdentificationTagSummary",
    "LifeStageCreateRequest",
    "LifeStageResponse",
    "LifeStageUpdateRequest",
    "ManagementUnitCreateRequest",
    "ManagementUnitResponse",
    "ManagementUnitSummary",
    "ManagementUnitTypeCreateRequest",
    "ManagementUnitTypeResponse",
    "ManagementUnitTypeUpdateRequest",
    "OriginCreateRequest",
    "OriginResponse",
    "OriginUpdateRequest",
    "PetCreateRequest",
    "PetListFilters",
    "PetListResponse",
    "PetResponse",
    "PetUpdateRequest",
    "SpeciesCreateRequest",
    "SpeciesResponse",
    "SpeciesSummary",
    "SpeciesUpdateRequest",
    "TagCreateRequest",
    "TagResponse",
    "TagUpdateRequest",
]
