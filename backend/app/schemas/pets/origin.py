from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..base import BaseRequestSchema


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
