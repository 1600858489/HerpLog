from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import (
    IdentificationTag,
    ManagementUnit,
    PersonalSpecies,
    Pet,
    PetIdentificationTag,
    PetManagementAssignment,
    PetOrigin,
)
from ...schemas.pets import PetListFilters


async def get_pet_by_uuid(session: AsyncSession, user_id: int, pet_uuid: UUID, detail: bool = False) -> Pet | None:
    """Return an active user-owned pet with scenario-specific eager loading."""
    options = [selectinload(Pet.species), selectinload(Pet.identification_tags), selectinload(Pet.assignments).selectinload(PetManagementAssignment.management_unit)]
    if detail:
        options.extend([
            selectinload(Pet.genes),
            selectinload(Pet.origins).selectinload(PetOrigin.parent_pet),
            selectinload(Pet.life_stages),
        ])

    result = await session.execute(select(Pet).where(
        Pet.uuid == pet_uuid, Pet.user_id == user_id, Pet.deleted_at.is_(None)
    ).options(*options))
    return result.scalar_one_or_none()


async def list_pets(session: AsyncSession, user_id: int, params, filters: PetListFilters) -> tuple[list[Pet], int]:
    """Return a filtered, paginated page of active user-owned pets."""
    query = select(Pet).where(Pet.user_id == user_id, Pet.deleted_at.is_(None))
    if filters.species_uuid:
        query = query.join(PersonalSpecies).where(PersonalSpecies.uuid == filters.species_uuid)
    if filters.sex:
        query = query.where(Pet.sex == filters.sex)
    if filters.management_unit_uuid or filters.assigned is not None:
        assignment_exists = select(PetManagementAssignment.id).join(ManagementUnit).where(
            PetManagementAssignment.pet_id == Pet.id, PetManagementAssignment.deleted_at.is_(None),
            PetManagementAssignment.ended_at.is_(None), ManagementUnit.user_id == user_id,
            ManagementUnit.deleted_at.is_(None),
        )
        if filters.management_unit_uuid:
            assignment_exists = assignment_exists.where(ManagementUnit.uuid == filters.management_unit_uuid)
        query = query.where(assignment_exists.exists() if filters.assigned is not False else ~assignment_exists.exists())
    if filters.tag_uuid:
        query = query.join(PetIdentificationTag).join(IdentificationTag).where(
            IdentificationTag.uuid == filters.tag_uuid, IdentificationTag.user_id == user_id
        )
    if filters.keyword:
        pattern = f"%{filters.keyword.strip()}%"
        query = query.where(or_(Pet.pet_code.ilike(pattern), Pet.name.ilike(pattern)))
    query = query.order_by(Pet.created_at.desc(), Pet.id.desc())
    result = await session.execute(query.options(
        selectinload(Pet.species), selectinload(Pet.identification_tags),
        selectinload(Pet.assignments).selectinload(PetManagementAssignment.management_unit),
    ).offset((params.page - 1) * params.page_size).limit(params.page_size))
    count = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().unique().all()), count.scalar_one()


async def get_active_pet_ids_by_management_unit(session: AsyncSession, user_id: int, management_unit_uuid: UUID) -> list[int]:
    """Return current internal pet IDs for one user-owned management unit."""
    result = await session.execute(select(Pet.id).join(PetManagementAssignment, PetManagementAssignment.pet_id == Pet.id).join(
        ManagementUnit, ManagementUnit.id == PetManagementAssignment.management_unit_id
    ).where(
        Pet.user_id == user_id, Pet.deleted_at.is_(None), ManagementUnit.user_id == user_id,
        ManagementUnit.uuid == management_unit_uuid, ManagementUnit.deleted_at.is_(None),
        PetManagementAssignment.deleted_at.is_(None), PetManagementAssignment.ended_at.is_(None),
    ))
    return list(result.scalars().all())
