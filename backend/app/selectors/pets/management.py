from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import ManagementUnit, ManagementUnitType, Pet, PetManagementAssignment


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


async def list_management_units(session: AsyncSession, user_id: int) -> list[ManagementUnit]:
    """Return active management units owned by the current user."""
    result = await session.execute(
        select(ManagementUnit)
        .where(ManagementUnit.user_id == user_id, ManagementUnit.deleted_at.is_(None))
        .options(selectinload(ManagementUnit.unit_type))
        .order_by(ManagementUnit.unit_code, ManagementUnit.id)
    )
    return list(result.scalars().all())


async def get_management_unit_type_by_uuid(
    session: AsyncSession, user_id: int, type_uuid: UUID
) -> ManagementUnitType | None:
    """Return a visible system or user-owned management-unit type."""
    result = await session.execute(
        select(ManagementUnitType).where(
            ManagementUnitType.uuid == type_uuid,
            ManagementUnitType.deleted_at.is_(None),
            (ManagementUnitType.is_system.is_(True) | (ManagementUnitType.user_id == user_id)),
        )
    )
    return result.scalar_one_or_none()


async def list_management_unit_members(
    session: AsyncSession, user_id: int, unit_uuid: UUID
) -> list[Pet]:
    """Return pets with a current assignment in one user-owned unit."""
    result = await session.execute(
        select(Pet)
        .join(PetManagementAssignment)
        .join(ManagementUnit)
        .where(
            ManagementUnit.uuid == unit_uuid,
            ManagementUnit.user_id == user_id,
            ManagementUnit.deleted_at.is_(None),
            Pet.user_id == user_id,
            Pet.deleted_at.is_(None),
            PetManagementAssignment.deleted_at.is_(None),
            PetManagementAssignment.ended_at.is_(None),
        )
        .options(
            selectinload(Pet.species),
            selectinload(Pet.identification_tags),
            selectinload(Pet.assignments).selectinload(PetManagementAssignment.management_unit),
        )
        .order_by(Pet.pet_code, Pet.id)
    )
    return list(result.scalars().unique().all())
