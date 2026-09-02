from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.pagination import PaginationParams
from ...models import IdentificationTag, PersonalGene, PersonalSpecies


async def get_species_by_uuid(session: AsyncSession, user_id: int, species_uuid: UUID) -> PersonalSpecies | None:
    """Return one active species owned by the current user."""
    result = await session.execute(select(PersonalSpecies).where(
        PersonalSpecies.uuid == species_uuid, PersonalSpecies.user_id == user_id, PersonalSpecies.deleted_at.is_(None)
    ))
    return result.scalar_one_or_none()


async def list_species(session: AsyncSession, user_id: int, params: PaginationParams, keyword: str | None = None) -> tuple[list[PersonalSpecies], int]:
    """Return a paginated page of active user-owned species."""
    query = select(PersonalSpecies).where(PersonalSpecies.user_id == user_id, PersonalSpecies.deleted_at.is_(None))
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.where(or_(PersonalSpecies.common_name.ilike(pattern), PersonalSpecies.scientific_name.ilike(pattern)))
    query = query.order_by(PersonalSpecies.common_name, PersonalSpecies.id)
    result = await session.execute(query.offset((params.page - 1) * params.page_size).limit(params.page_size))
    count = await session.execute(select(func.count()).select_from(query.order_by(None).subquery()))
    return list(result.scalars().all()), count.scalar_one()


async def get_gene_by_uuid(session: AsyncSession, user_id: int, gene_uuid: UUID) -> PersonalGene | None:
    """Return one active personal gene owned by the current user."""
    result = await session.execute(select(PersonalGene).where(
        PersonalGene.uuid == gene_uuid, PersonalGene.user_id == user_id, PersonalGene.deleted_at.is_(None)
    ))
    return result.scalar_one_or_none()


async def get_tag_by_uuid(session: AsyncSession, user_id: int, tag_uuid: UUID) -> IdentificationTag | None:
    """Return one active identification tag owned by the current user."""
    result = await session.execute(select(IdentificationTag).where(
        IdentificationTag.uuid == tag_uuid, IdentificationTag.user_id == user_id, IdentificationTag.deleted_at.is_(None)
    ))
    return result.scalar_one_or_none()


async def list_genes(session: AsyncSession, user_id: int) -> list[PersonalGene]:
    """Return active reusable genes owned by the current user."""
    result = await session.execute(
        select(PersonalGene)
        .where(PersonalGene.user_id == user_id, PersonalGene.deleted_at.is_(None))
        .order_by(PersonalGene.name, PersonalGene.id)
    )
    return list(result.scalars().all())


async def list_tags(session: AsyncSession, user_id: int) -> list[IdentificationTag]:
    """Return active identification tags owned by the current user."""
    result = await session.execute(
        select(IdentificationTag)
        .where(IdentificationTag.user_id == user_id, IdentificationTag.deleted_at.is_(None))
        .order_by(IdentificationTag.name, IdentificationTag.id)
    )
    return list(result.scalars().all())
