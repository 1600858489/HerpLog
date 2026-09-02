from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...models import (
    ManagementUnit,
    Pet,
    PetLifeStage,
    PetManagementAssignment,
    PetOrigin,
    PetOriginType,
    PetParentRole,
)
from ...schemas.pets import (
    AssignmentCreateRequest,
    AssignmentMoveRequest,
    LifeStageCreateRequest,
    LifeStageUpdateRequest,
    OriginCreateRequest,
    OriginUpdateRequest,
)
from ...selectors import get_management_unit_by_uuid, get_pet_by_uuid
from ...utils.datetime import utc_now


async def _get_active_assignment(
    session: AsyncSession, user_id: int, pet_uuid: UUID
) -> PetManagementAssignment | None:
    """Return the current assignment for one user-owned pet."""
    result = await session.execute(
        select(PetManagementAssignment)
        .join(Pet)
        .where(
            Pet.uuid == pet_uuid,
            Pet.user_id == user_id,
            Pet.deleted_at.is_(None),
            PetManagementAssignment.deleted_at.is_(None),
            PetManagementAssignment.ended_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_assignment(
    session: AsyncSession, user_id: int, pet_uuid: UUID, request: AssignmentCreateRequest
) -> PetManagementAssignment:
    """Assign a user-owned pet to a management unit."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    unit = await get_management_unit_by_uuid(session, user_id, request.management_unit_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    if unit is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_NOT_FOUND)
    if await _get_active_assignment(session, user_id, pet_uuid) is not None:
        raise BusinessError(ErrorCode.ORIGIN_OR_ASSIGNMENT_INVALID_STATE)
    assignment = PetManagementAssignment(
        pet_id=pet.id,
        management_unit_id=unit.id,
        started_at=request.started_at,
        life_stage=request.life_stage,
        transfer_reason=request.transfer_reason,
        note=request.note,
    )
    session.add(assignment)
    await session.flush()
    return assignment


async def move_pet(
    session: AsyncSession, user_id: int, pet_uuid: UUID, request: AssignmentMoveRequest
) -> PetManagementAssignment:
    """End the current assignment and create a new historical assignment."""
    current = await _get_active_assignment(session, user_id, pet_uuid)
    if current is None:
        return await create_assignment(session, user_id, pet_uuid, request)
    target = await get_management_unit_by_uuid(session, user_id, request.management_unit_uuid)
    if target is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_NOT_FOUND)
    if target.id == current.management_unit_id:
        raise BusinessError(ErrorCode.ORIGIN_OR_ASSIGNMENT_INVALID_STATE)
    current.ended_at = request.started_at
    await session.flush()
    return await create_assignment(session, user_id, pet_uuid, request)


async def remove_pet_from_management_unit(
    session: AsyncSession, user_id: int, pet_uuid: UUID, ended_at: datetime
) -> None:
    """End the current assignment while preserving the pet and its history."""
    current = await _get_active_assignment(session, user_id, pet_uuid)
    if current is None:
        raise BusinessError(ErrorCode.ORIGIN_OR_ASSIGNMENT_NOT_FOUND)
    current.ended_at = ended_at
    await session.flush()


async def create_life_stage(
    session: AsyncSession, user_id: int, pet_uuid: UUID, request: LifeStageCreateRequest
) -> PetLifeStage:
    """Create a new life-stage interval after ending the current interval."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    current_result = await session.execute(
        select(PetLifeStage)
        .where(
            PetLifeStage.pet_id == pet.id,
            PetLifeStage.deleted_at.is_(None),
            PetLifeStage.ended_at.is_(None),
        )
    )
    current = current_result.scalar_one_or_none()
    if current is not None:
        if request.started_at <= current.started_at:
            raise BusinessError(ErrorCode.ORIGIN_OR_ASSIGNMENT_INVALID_STATE)
        current.ended_at = request.started_at
    stage = PetLifeStage(
        pet_id=pet.id,
        stage=request.stage,
        started_at=request.started_at,
        change_reason=request.change_reason,
        note=request.note,
    )
    session.add(stage)
    await session.flush()
    return stage


async def end_life_stage(
    session: AsyncSession,
    user_id: int,
    pet_uuid: UUID,
    stage_uuid: UUID,
    ended_at: datetime,
) -> PetLifeStage:
    """End one active life-stage interval for a user-owned pet."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    result = await session.execute(
        select(PetLifeStage).where(
            PetLifeStage.uuid == stage_uuid,
            PetLifeStage.pet_id == pet.id,
            PetLifeStage.deleted_at.is_(None),
            PetLifeStage.ended_at.is_(None),
        )
    )
    stage = result.scalar_one_or_none()
    if stage is None:
        raise BusinessError(ErrorCode.PET_STATE_NOT_FOUND)
    if ended_at <= stage.started_at:
        raise BusinessError(ErrorCode.PET_STATE_VALIDATION_FAILED)
    stage.ended_at = ended_at
    await session.flush()
    return stage


async def create_origin(
    session: AsyncSession, user_id: int, pet_uuid: UUID, request: OriginCreateRequest
) -> PetOrigin:
    """Create a source or parent claim for a user-owned pet."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    parent_pet_id = None
    if request.parent_pet_uuid is not None:
        parent = await get_pet_by_uuid(session, user_id, request.parent_pet_uuid)
        if parent is None or parent.id == pet.id:
            raise BusinessError(ErrorCode.ORIGIN_OR_ASSIGNMENT_INVALID_STATE)
        parent_pet_id = parent.id
    origin = PetOrigin(
        pet_id=pet.id,
        origin_type=request.origin_type,
        parent_role=request.parent_role,
        parent_pet_id=parent_pet_id,
        breeder_name=request.breeder_name,
        external_name=request.external_name,
        genetic_note=request.genetic_note,
        confidence=request.confidence,
        note=request.note,
    )
    session.add(origin)
    await session.flush()
    return origin


async def update_origin(
    session: AsyncSession,
    user_id: int,
    pet_uuid: UUID,
    origin_uuid: UUID,
    request: OriginUpdateRequest,
) -> PetOrigin:
    """Update one source or parent claim belonging to a user-owned pet."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    result = await session.execute(
        select(PetOrigin).where(
            PetOrigin.uuid == origin_uuid,
            PetOrigin.pet_id == pet.id,
            PetOrigin.deleted_at.is_(None),
        )
    )
    origin = result.scalar_one_or_none()
    if origin is None:
        raise BusinessError(ErrorCode.ORIGIN_OR_ASSIGNMENT_NOT_FOUND)
    for field, value in request.model_dump().items():
        if field == "parent_pet_uuid":
            continue
        setattr(origin, field, value)
    await session.flush()
    return origin


async def soft_delete_origin(
    session: AsyncSession, user_id: int, pet_uuid: UUID, origin_uuid: UUID
) -> None:
    """Soft-delete one source record belonging to a user-owned pet."""
    origin = await update_origin(
        session,
        user_id,
        pet_uuid,
        origin_uuid,
        OriginUpdateRequest(origin_type=PetOriginType.UNKNOWN.value),
    )
    origin.deleted_at = utc_now()
    await session.flush()


__all__ = [
    "create_assignment",
    "create_life_stage",
    "create_origin",
    "end_life_stage",
    "move_pet",
    "remove_pet_from_management_unit",
    "soft_delete_origin",
    "update_origin",
]
