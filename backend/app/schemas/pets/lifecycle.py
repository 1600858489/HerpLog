from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..base import BaseRequestSchema
from .management import ManagementUnitSummary


class AssignmentCreateRequest(BaseRequestSchema):
    """Validate adding a pet to a management unit."""

    management_unit_uuid: UUID
    started_at: datetime
    life_stage: str | None = None
    transfer_reason: str | None = None
    note: str | None = None


class AssignmentMoveRequest(AssignmentCreateRequest):
    """Validate moving a pet to another management unit."""


class AssignmentResponse(BaseModel):
    """Serialize one historical management assignment."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
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


class LifeStageResponse(BaseModel):
    """Serialize one historical life-stage interval."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    stage: str
    started_at: datetime
    ended_at: datetime | None
    change_reason: str | None
    note: str | None


__all__ = [
    "AssignmentCreateRequest", "AssignmentMoveRequest", "AssignmentResponse",
    "LifeStageCreateRequest", "LifeStageResponse", "LifeStageUpdateRequest",
]
