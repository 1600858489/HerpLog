from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import ConfidenceLevel, PetOriginType, PetParentRole
from ..base import BaseRequestSchema


class OriginCreateRequest(BaseRequestSchema):
    """Validate one source or parent claim for a pet."""

    origin_type: PetOriginType
    parent_role: PetParentRole = PetParentRole.UNSPECIFIED
    parent_pet_uuid: UUID | None = None
    breeder_name: str | None = None
    external_name: str | None = None
    genetic_note: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    note: str | None = None


class OriginUpdateRequest(BaseRequestSchema):
    """Validate optional updates to a source or parent claim."""

    origin_type: PetOriginType | None = None
    parent_role: PetParentRole | None = None
    parent_pet_uuid: UUID | None = None
    breeder_name: str | None = None
    external_name: str | None = None
    genetic_note: str | None = None
    confidence: ConfidenceLevel | None = None
    note: str | None = None


class OriginResponse(BaseModel):
    """Serialize one source or parent claim."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    origin_type: str
    parent_role: str
    parent_pet_uuid: UUID | None
    breeder_name: str | None
    external_name: str | None
    genetic_note: str | None
    confidence: str
    note: str | None


__all__ = ["OriginCreateRequest", "OriginResponse", "OriginUpdateRequest"]
