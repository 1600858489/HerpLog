from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...models import ManagementUnit, ManagementUnitType, PetManagementAssignment
from ...schemas.pets import ManagementUnitTypeUpdateRequest
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
    result = await session.execute(
        select(ManagementUnitType).where(
            ManagementUnitType.uuid == type_uuid,
            ManagementUnitType.deleted_at.is_(None),
            (ManagementUnitType.is_system.is_(True) | (ManagementUnitType.user_id == user_id)),
        )
    )
    return result.scalar_one_or_none()


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
    unit_type.name = request.name
    await session.flush()
    return unit_type


async def clear_and_delete_management_unit(
    session: AsyncSession, user_id: int, unit_uuid: UUID
) -> None:
    """End all active assignments and soft-delete one user-owned unit."""
    result = await session.execute(
        select(ManagementUnit).where(
            ManagementUnit.uuid == unit_uuid,
            ManagementUnit.user_id == user_id,
            ManagementUnit.deleted_at.is_(None),
        )
    )
    unit = result.scalar_one_or_none()
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


__all__ = ["clear_and_delete_management_unit", "update_management_unit_type"]
