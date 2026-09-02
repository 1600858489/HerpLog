from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..base import BaseRequestSchema


class ManagementUnitTypeCreateRequest(BaseRequestSchema):
    """Validate a user-defined management-unit type."""

    name: str = Field(min_length=1, max_length=255)


class ManagementUnitTypeUpdateRequest(ManagementUnitTypeCreateRequest):
    """Validate an editable management-unit type."""


class ManagementUnitTypeResponse(BaseModel):
    """Serialize a management-unit type."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    is_system: bool


class ManagementUnitCreateRequest(BaseRequestSchema):
    """Validate a flat management-unit creation request."""

    type_uuid: UUID
    unit_code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=1000)


class ManagementUnitUpdateRequest(BaseRequestSchema):
    """Validate editable management-unit fields."""

    unit_code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=1000)


class ManagementUnitSummary(BaseModel):
    """Serialize the compact management-unit fields used by pet lists."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str | None
    unit_code: str


class ManagementUnitResponse(ManagementUnitSummary):
    """Serialize a flat management unit and its type."""

    type: ManagementUnitTypeResponse


__all__ = [
    "ManagementUnitCreateRequest", "ManagementUnitResponse", "ManagementUnitSummary",
    "ManagementUnitTypeCreateRequest", "ManagementUnitTypeResponse",
    "ManagementUnitTypeUpdateRequest", "ManagementUnitUpdateRequest",
]
