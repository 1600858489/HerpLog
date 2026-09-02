from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ...models import PetSex
from ..base import BaseRequestSchema
from .classification import GeneResponse, IdentificationTagSummary, SpeciesSummary
from .lifecycle import AssignmentResponse, LifeStageResponse
from .management import ManagementUnitSummary
from .origin import OriginResponse


class PetCreateRequest(BaseRequestSchema):
    """Validate creation of a pet identified by a personal species."""

    species_uuid: UUID
    sex: PetSex = PetSex.UNKNOWN
    name: str | None = Field(default=None, max_length=255)
    pet_code: str | None = Field(default=None, max_length=64)
    identification_note: str | None = Field(default=None, max_length=1000)
    owner_note: str | None = Field(default=None, max_length=1000)
    gene_uuids: list[UUID] = Field(default_factory=list)
    tag_uuids: list[UUID] = Field(default_factory=list)


class PetUpdateRequest(BaseRequestSchema):
    """Validate editable pet base fields."""

    species_uuid: UUID | None = None
    sex: PetSex | None = None
    name: str | None = Field(default=None, max_length=255)
    pet_code: str | None = Field(default=None, max_length=64)
    identification_note: str | None = Field(default=None, max_length=1000)
    owner_note: str | None = Field(default=None, max_length=1000)


class PetListFilters(BaseModel):
    """Represent validated pet list filters."""

    species_uuid: UUID | None = None
    sex: str | None = None
    management_unit_uuid: UUID | None = None
    assigned: bool | None = None
    tag_uuid: UUID | None = None
    keyword: str | None = None


class PetListResponse(BaseModel):
    """Serialize the compact pet list representation."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    pet_code: str
    name: str | None
    species: SpeciesSummary
    sex: str
    current_management_unit: ManagementUnitSummary | None
    identification_tags: list[IdentificationTagSummary]


class PetResponse(PetListResponse):
    """Serialize one pet with its complete managed history."""

    identification_note: str | None
    owner_note: str | None
    genes: list[GeneResponse]
    origins: list[OriginResponse]
    life_stages: list[LifeStageResponse]
    management_assignments: list[AssignmentResponse]


__all__ = ["PetCreateRequest", "PetListFilters", "PetListResponse", "PetResponse", "PetUpdateRequest"]
