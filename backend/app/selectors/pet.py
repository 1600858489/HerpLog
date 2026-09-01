from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.pagination import PaginationParams
from ..models import (
    IdentificationTag,
    ManagementUnit,
    ManagementUnitType,
    PersonalGene,
    PersonalSpecies,
    Pet,
    PetLifeStage,
    PetManagementAssignment,
    PetOrigin,
)
from ..schemas.pet import PetListFilters


async def get_species_by_uuid(
    session: AsyncSession, user_id: int, species_uuid: UUID
) -> PersonalSpecies | None:
    """Return one active species owned by the current user."""
    result = await session.execute(
        select(PersonalSpecies).where(
            PersonalSpecies.uuid == species_uuid,
            PersonalSpecies.user_id == user_id,
            PersonalSpecies.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_species(
    session: AsyncSession,
    user_id: int,
    params: PaginationParams,
    keyword: str | None = None,
) -> tuple[list[PersonalSpecies], int]:
    """Return one paginated page of active user-owned species."""
    query = select(PersonalSpecies).where(
        PersonalSpecies.user_id == user_id,
        PersonalSpecies.deleted_at.is_(None),
    )
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                PersonalSpecies.common_name.ilike(pattern),
                PersonalSpecies.scientific_name.ilike(pattern),
            )
        )
    query = query.order_by(PersonalSpecies.common_name, PersonalSpecies.id)
    result = await session.execute(
        query.offset((params.page - 1) * params.page_size).limit(params.page_size)
    )
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    count_result = await session.execute(count_query)
    return list(result.scalars().all()), count_result.scalar_one()


async def get_gene_by_uuid(session: AsyncSession, user_id: int, gene_uuid: UUID) -> PersonalGene | None:
    """Return one active personal gene owned by the current user."""
    result = await session.execute(
        select(PersonalGene).where(
            PersonalGene.uuid == gene_uuid,
            PersonalGene.user_id == user_id,
            PersonalGene.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_tag_by_uuid(session: AsyncSession, user_id: int, tag_uuid: UUID) -> IdentificationTag | None:
    """Return one active identification tag owned by the current user."""
    result = await session.execute(
        select(IdentificationTag).where(
            IdentificationTag.uuid == tag_uuid,
            IdentificationTag.user_id == user_id,
            IdentificationTag.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_management_unit_by_uuid(
    session: AsyncSession, user_id: int, unit_uuid: UUID
) -> ManagementUnit | None:
    """Return one active management unit owned by the current user."""
    result = await session.execute(
        select(ManagementUnit)
        .where(
            ManagementUnit.uuid == unit_uuid,
            ManagementUnit.user_id == user_id,
            ManagementUnit.deleted_at.is_(None),
        )
        .options(selectinload(ManagementUnit.unit_type))
    )
    return result.scalar_one_or_none()


async def get_pet_by_uuid(
    session: AsyncSession, user_id: int, pet_uuid: UUID, detail: bool = False
) -> Pet | None:
    """Return an active user-owned pet with scenario-specific eager loading."""
    options = [selectinload(Pet.species), selectinload(Pet.identification_tags)]
    if detail:
        options.extend(
            [
                selectinload(Pet.genes),
                selectinload(Pet.origins),
                selectinload(Pet.life_stages),
                selectinload(Pet.assignments).selectinload(PetManagementAssignment.management_unit),
            ]
        )
    result = await session.execute(
        select(Pet)
        .where(Pet.uuid == pet_uuid, Pet.user_id == user_id, Pet.deleted_at.is_(None))
        .options(*options)
    )
    return result.scalar_one_or_none()


async def list_pets(
    session: AsyncSession,
    user_id: int,
    params: PaginationParams,
    filters: PetListFilters,
) -> tuple[list[Pet], int]:
    """Return a filtered, paginated page of active user-owned pets."""
    query = select(Pet).where(Pet.user_id == user_id, Pet.deleted_at.is_(None))
    if filters.species_uuid:
        query = query.join(PersonalSpecies).where(PersonalSpecies.uuid == filters.species_uuid)
    if filters.sex:
        query = query.where(Pet.sex == filters.sex)
    if filters.management_unit_uuid or filters.assigned is not None:
        assignment_exists = (
            select(PetManagementAssignment.id)
            .join(ManagementUnit)
            .where(
                PetManagementAssignment.pet_id == Pet.id,
                PetManagementAssignment.deleted_at.is_(None),
                PetManagementAssignment.ended_at.is_(None),
                ManagementUnit.user_id == user_id,
                ManagementUnit.deleted_at.is_(None),
            )
        )
        if filters.management_unit_uuid:
            assignment_exists = assignment_exists.where(ManagementUnit.uuid == filters.management_unit_uuid)
        query = query.where(assignment_exists.exists() if filters.assigned is not False else ~assignment_exists.exists())
    if filters.tag_uuid:
        query = query.join(PetIdentificationTag).join(IdentificationTag).where(
            IdentificationTag.uuid == filters.tag_uuid,
            IdentificationTag.user_id == user_id,
        )
    if filters.keyword:
        pattern = f"%{filters.keyword.strip()}%"
        query = query.where(or_(Pet.pet_code.ilike(pattern), Pet.name.ilike(pattern)))
    query = query.order_by(Pet.created_at.desc(), Pet.id.desc())
    result = await session.execute(
        query.options(selectinload(Pet.species), selectinload(Pet.identification_tags))
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    count_result = await session.execute(
        select(func.count()).select_from(query.order_by(None).subquery())
    )
    return list(result.scalars().unique().all()), count_result.scalar_one()


async def list_pet_assignments(
    session: AsyncSession, user_id: int, pet_uuid: UUID, params: PaginationParams
) -> tuple[list[PetManagementAssignment], int]:
    """Return assignment history for a user-owned pet."""
    query = (
        select(PetManagementAssignment)
        .join(Pet)
        .where(
            Pet.uuid == pet_uuid,
            Pet.user_id == user_id,
            Pet.deleted_at.is_(None),
            PetManagementAssignment.deleted_at.is_(None),
        )
        .options(selectinload(PetManagementAssignment.management_unit).selectinload(ManagementUnit.unit_type))
        .order_by(PetManagementAssignment.started_at.desc(), PetManagementAssignment.id.desc())
    )
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count_result = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count_result.scalar_one()


async def list_pet_life_stages(
    session: AsyncSession, user_id: int, pet_uuid: UUID, params: PaginationParams
) -> tuple[list[PetLifeStage], int]:
    """Return life-stage history for a user-owned pet."""
    query = select(PetLifeStage).join(Pet).where(
        Pet.uuid == pet_uuid,
        Pet.user_id == user_id,
        Pet.deleted_at.is_(None),
        PetLifeStage.deleted_at.is_(None),
    ).order_by(PetLifeStage.started_at.desc(), PetLifeStage.id.desc())
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count_result = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count_result.scalar_one()


async def list_pet_origins(
    session: AsyncSession, user_id: int, pet_uuid: UUID, params: PaginationParams
) -> tuple[list[PetOrigin], int]:
    """Return origin history for a user-owned pet."""
    query = select(PetOrigin).join(Pet, PetOrigin.pet_id == Pet.id).where(
        Pet.uuid == pet_uuid,
        Pet.user_id == user_id,
        Pet.deleted_at.is_(None),
        PetOrigin.deleted_at.is_(None),
    ).options(selectinload(PetOrigin.parent_pet)).order_by(PetOrigin.created_at.desc(), PetOrigin.id.desc())
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count_result = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count_result.scalar_one()


async def get_active_pet_ids_by_management_unit(
    session: AsyncSession, user_id: int, management_unit_uuid: UUID
) -> list[int]:
    """Return current internal pet IDs for one user-owned management unit."""
    result = await session.execute(
        select(Pet.id)
        .join(PetManagementAssignment, PetManagementAssignment.pet_id == Pet.id)
        .join(ManagementUnit, ManagementUnit.id == PetManagementAssignment.management_unit_id)
        .where(
            Pet.user_id == user_id,
            Pet.deleted_at.is_(None),
            ManagementUnit.user_id == user_id,
            ManagementUnit.uuid == management_unit_uuid,
            ManagementUnit.deleted_at.is_(None),
            PetManagementAssignment.deleted_at.is_(None),
            PetManagementAssignment.ended_at.is_(None),
        )
    )
    return list(result.scalars().all())


__all__ = [
    "get_active_pet_ids_by_management_unit",
    "get_gene_by_uuid",
    "get_management_unit_by_uuid",
    "get_pet_by_uuid",
    "get_species_by_uuid",
    "get_tag_by_uuid",
    "list_pet_assignments",
    "list_pet_life_stages",
    "list_pet_origins",
    "list_pets",
    "list_species",
]
