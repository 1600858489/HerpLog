from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...models import ManagementUnit, ManagementUnitType, PetManagementAssignment
from ...schemas.pets import (
    ManagementUnitCreateRequest,
    ManagementUnitTypeCreateRequest,
    ManagementUnitTypeUpdateRequest,
    ManagementUnitUpdateRequest,
)
from ...selectors import get_management_unit_type_by_uuid
from ...utils.datetime import utc_now


async def _get_user_unit_type(
    session: AsyncSession, user_id: int, type_uuid: UUID
) -> ManagementUnitType | None:
    result = await session.execute(
        select(ManagementUnitType).where(
            ManagementUnitType.uuid == type_uuid,
            ManagementUnitType.user_id == user_id,
            ManagementUnitType.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _get_visible_unit_type(
    session: AsyncSession, user_id: int, type_uuid: UUID
) -> ManagementUnitType | None:
    return await get_management_unit_type_by_uuid(session, user_id, type_uuid)


async def _get_unit(
    session: AsyncSession, user_id: int, unit_uuid: UUID
) -> ManagementUnit | None:
    result = await session.execute(
        select(ManagementUnit).where(
            ManagementUnit.uuid == unit_uuid,
            ManagementUnit.user_id == user_id,
            ManagementUnit.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _generate_unit_code(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(
        select(ManagementUnit.unit_code)
        .where(ManagementUnit.user_id == user_id)
        .order_by(ManagementUnit.id.desc())
        .limit(1)
    )
    latest_code = result.scalar_one_or_none()
    next_number = 1
    if latest_code and latest_code.startswith("UNIT-") and latest_code[5:].isdigit():
        next_number = int(latest_code[5:]) + 1
    return f"UNIT-{next_number:03d}"


async def create_management_unit_type(
    session: AsyncSession, user_id: int, request: ManagementUnitTypeCreateRequest
) -> ManagementUnitType:
    """Create one reusable management-unit type owned by the current user."""
    existing = await session.execute(
        select(ManagementUnitType).where(
            ManagementUnitType.name == request.name,
            ManagementUnitType.deleted_at.is_(None),
            (ManagementUnitType.is_system.is_(True) | (ManagementUnitType.user_id == user_id)),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_CONFLICT)
    unit_type = ManagementUnitType(user_id=user_id, name=request.name, is_system=False)
    session.add(unit_type)
    await session.flush()
    return unit_type


async def update_management_unit_type(
    session: AsyncSession,
    user_id: int,
    type_uuid: UUID,
    request: ManagementUnitTypeUpdateRequest,
) -> ManagementUnitType:
    """Update a user-owned type while rejecting system types."""
    unit_type = await _get_visible_unit_type(session, user_id, type_uuid)
    if unit_type is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_NOT_FOUND)
    if unit_type.is_system:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_FORBIDDEN)
    duplicate = await session.execute(
        select(ManagementUnitType).where(
            ManagementUnitType.name == request.name,
            ManagementUnitType.uuid != type_uuid,
            ManagementUnitType.deleted_at.is_(None),
            (ManagementUnitType.is_system.is_(True) | (ManagementUnitType.user_id == user_id)),
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_CONFLICT)
    unit_type.name = request.name
    await session.flush()
    return unit_type


async def soft_delete_management_unit_type(
    session: AsyncSession, user_id: int, type_uuid: UUID
) -> None:
    """Soft-delete one user-owned management-unit type."""
    unit_type = await _get_visible_unit_type(session, user_id, type_uuid)
    if unit_type is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_NOT_FOUND)
    if unit_type.is_system:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_FORBIDDEN)
    unit_type.deleted_at = utc_now()
    await session.flush()


async def create_management_unit(
    session: AsyncSession, user_id: int, request: ManagementUnitCreateRequest
) -> ManagementUnit:
    """Create a flat management unit using a visible type."""
    unit_type = await _get_visible_unit_type(session, user_id, request.type_uuid)
    if unit_type is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_TYPE_NOT_FOUND)
    unit_code = request.unit_code or await _generate_unit_code(session, user_id)
    duplicate = await session.execute(
        select(ManagementUnit).where(
            ManagementUnit.user_id == user_id,
            ManagementUnit.unit_code == unit_code,
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_CONFLICT)
    unit = ManagementUnit(
        user_id=user_id,
        type_id=unit_type.id,
        unit_code=unit_code,
        name=request.name,
        note=request.note,
    )
    session.add(unit)
    await session.flush()
    return unit


async def update_management_unit(
    session: AsyncSession, user_id: int, unit_uuid: UUID, request: ManagementUnitUpdateRequest
) -> ManagementUnit:
    """Update editable fields for one current user's management unit."""
    unit = await _get_unit(session, user_id, unit_uuid)
    if unit is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_NOT_FOUND)
    if request.unit_code is not None and request.unit_code != unit.unit_code:
        duplicate = await session.execute(
            select(ManagementUnit).where(
                ManagementUnit.user_id == user_id,
                ManagementUnit.unit_code == request.unit_code,
                ManagementUnit.uuid != unit_uuid,
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise BusinessError(ErrorCode.MANAGEMENT_UNIT_CONFLICT)
        unit.unit_code = request.unit_code
    for field in ("name", "note"):
        value = getattr(request, field)
        if value is not None:
            setattr(unit, field, value)
    await session.flush()
    return unit


async def soft_delete_management_unit(
    session: AsyncSession, user_id: int, unit_uuid: UUID
) -> None:
    """Soft-delete an unassigned management unit without changing history."""
    unit = await _get_unit(session, user_id, unit_uuid)
    if unit is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_NOT_FOUND)
    active_assignment = await session.scalar(
        select(PetManagementAssignment.id).where(
            PetManagementAssignment.management_unit_id == unit.id,
            PetManagementAssignment.deleted_at.is_(None),
            PetManagementAssignment.ended_at.is_(None),
        )
    )
    if active_assignment is not None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_INVALID_STATE)
    unit.deleted_at = utc_now()
    await session.flush()


async def clear_and_delete_management_unit(
    session: AsyncSession, user_id: int, unit_uuid: UUID
) -> None:
    """End all active assignments and soft-delete one user-owned unit."""
    unit = await _get_unit(session, user_id, unit_uuid)
    if unit is None:
        raise BusinessError(ErrorCode.MANAGEMENT_UNIT_NOT_FOUND)
    assignment_result = await session.execute(
        select(PetManagementAssignment).where(
            PetManagementAssignment.management_unit_id == unit.id,
            PetManagementAssignment.deleted_at.is_(None),
            PetManagementAssignment.ended_at.is_(None),
        )
    )
    ended_at = utc_now()
    for assignment in assignment_result.scalars():
        assignment.ended_at = ended_at
    unit.deleted_at = ended_at
    await session.flush()


__all__ = [
    "clear_and_delete_management_unit",
    "create_management_unit",
    "create_management_unit_type",
    "soft_delete_management_unit",
    "soft_delete_management_unit_type",
    "update_management_unit",
    "update_management_unit_type",
]
