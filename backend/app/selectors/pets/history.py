from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.pagination import PaginationParams
from ...models import ManagementUnit, Pet, PetLifeStage, PetManagementAssignment, PetOrigin


async def get_pet_assignment_by_uuid(
    session: AsyncSession, user_id: int, pet_uuid: UUID, assignment_uuid: UUID
) -> PetManagementAssignment | None:
    """Return one assignment record for a user-owned pet with its unit loaded."""
    result = await session.execute(
        select(PetManagementAssignment)
        .join(Pet)
        .where(
            Pet.uuid == pet_uuid,
            Pet.user_id == user_id,
            Pet.deleted_at.is_(None),
            PetManagementAssignment.uuid == assignment_uuid,
            PetManagementAssignment.deleted_at.is_(None),
        )
        .options(selectinload(PetManagementAssignment.management_unit))
    )
    return result.scalar_one_or_none()


async def list_pet_assignments(session: AsyncSession, user_id: int, pet_uuid: UUID, params: PaginationParams) -> tuple[list[PetManagementAssignment], int]:
    """Return assignment history for a user-owned pet."""
    query = select(PetManagementAssignment).join(Pet).where(
        Pet.uuid == pet_uuid, Pet.user_id == user_id, Pet.deleted_at.is_(None),
        PetManagementAssignment.deleted_at.is_(None),
    ).options(selectinload(PetManagementAssignment.management_unit).selectinload(ManagementUnit.unit_type)).order_by(
        PetManagementAssignment.started_at.desc(), PetManagementAssignment.id.desc()
    )
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count.scalar_one()


async def list_pet_life_stages(session: AsyncSession, user_id: int, pet_uuid: UUID, params: PaginationParams) -> tuple[list[PetLifeStage], int]:
    """Return life-stage history for a user-owned pet."""
    query = select(PetLifeStage).join(Pet).where(
        Pet.uuid == pet_uuid, Pet.user_id == user_id, Pet.deleted_at.is_(None), PetLifeStage.deleted_at.is_(None)
    ).order_by(PetLifeStage.started_at.desc(), PetLifeStage.id.desc())
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count.scalar_one()


async def get_pet_origin_by_uuid(
    session: AsyncSession, user_id: int, pet_uuid: UUID, origin_uuid: UUID
) -> PetOrigin | None:
    """Return one source record for a user-owned pet with its parent loaded."""
    result = await session.execute(
        select(PetOrigin)
        .join(Pet, PetOrigin.pet_id == Pet.id)
        .where(
            Pet.uuid == pet_uuid,
            Pet.user_id == user_id,
            Pet.deleted_at.is_(None),
            PetOrigin.uuid == origin_uuid,
            PetOrigin.deleted_at.is_(None),
        )
        .options(selectinload(PetOrigin.parent_pet))
    )
    return result.scalar_one_or_none()


async def list_pet_origins(session: AsyncSession, user_id: int, pet_uuid: UUID, params: PaginationParams) -> tuple[list[PetOrigin], int]:
    """Return origin history for a user-owned pet."""
    query = select(PetOrigin).join(Pet, PetOrigin.pet_id == Pet.id).where(
        Pet.uuid == pet_uuid, Pet.user_id == user_id, Pet.deleted_at.is_(None), PetOrigin.deleted_at.is_(None)
    ).options(selectinload(PetOrigin.parent_pet)).order_by(PetOrigin.created_at.desc(), PetOrigin.id.desc())
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count.scalar_one()
