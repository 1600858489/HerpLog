from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import ManagementUnit, ManagementUnitType


async def get_management_unit_by_uuid(session: AsyncSession, user_id: int, unit_uuid: UUID) -> ManagementUnit | None:
    """Return one active management unit owned by the current user."""
    result = await session.execute(select(ManagementUnit).where(
        ManagementUnit.uuid == unit_uuid, ManagementUnit.user_id == user_id, ManagementUnit.deleted_at.is_(None)
    ).options(selectinload(ManagementUnit.unit_type)))
    return result.scalar_one_or_none()


async def list_management_unit_types(session: AsyncSession, user_id: int) -> list[ManagementUnitType]:
    """Return active system and current-user management unit types."""
    result = await session.execute(select(ManagementUnitType).where(
        ManagementUnitType.deleted_at.is_(None),
        (ManagementUnitType.is_system.is_(True) | (ManagementUnitType.user_id == user_id)),
    ).order_by(ManagementUnitType.is_system.desc(), ManagementUnitType.name))
    return list(result.scalars().all())
