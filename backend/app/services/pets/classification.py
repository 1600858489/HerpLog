from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...models import IdentificationTag, PersonalGene, PersonalSpecies
from ...schemas.pets import (
    GeneCreateRequest,
    GeneUpdateRequest,
    SpeciesCreateRequest,
    SpeciesUpdateRequest,
    TagCreateRequest,
    TagUpdateRequest,
)
from ...utils.datetime import utc_now


async def _get_species(session: AsyncSession, user_id: int, resource_uuid: UUID) -> PersonalSpecies | None:
    result = await session.execute(
        select(PersonalSpecies).where(
            PersonalSpecies.uuid == resource_uuid,
            PersonalSpecies.user_id == user_id,
            PersonalSpecies.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _get_gene(session: AsyncSession, user_id: int, resource_uuid: UUID) -> PersonalGene | None:
    result = await session.execute(
        select(PersonalGene).where(
            PersonalGene.uuid == resource_uuid,
            PersonalGene.user_id == user_id,
            PersonalGene.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _get_tag(session: AsyncSession, user_id: int, resource_uuid: UUID) -> IdentificationTag | None:
    result = await session.execute(
        select(IdentificationTag).where(
            IdentificationTag.uuid == resource_uuid,
            IdentificationTag.user_id == user_id,
            IdentificationTag.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_species(session: AsyncSession, user_id: int, request: SpeciesCreateRequest) -> PersonalSpecies:
    """Create one normalized personal species entry."""
    existing = await session.execute(
        select(PersonalSpecies).where(
            PersonalSpecies.user_id == user_id,
            PersonalSpecies.common_name == request.common_name,
            PersonalSpecies.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise BusinessError(ErrorCode.SPECIES_CONFLICT)
    species = PersonalSpecies(user_id=user_id, **request.model_dump())
    session.add(species)
    await session.flush()
    return species


async def update_species(session: AsyncSession, user_id: int, species_uuid: UUID, request: SpeciesUpdateRequest) -> PersonalSpecies:
    """Update one active personal species entry."""
    species = await _get_species(session, user_id, species_uuid)
    if species is None:
        raise BusinessError(ErrorCode.SPECIES_NOT_FOUND)
    if request.common_name != species.common_name:
        duplicate = await session.execute(
            select(PersonalSpecies).where(
                PersonalSpecies.user_id == user_id,
                PersonalSpecies.common_name == request.common_name,
                PersonalSpecies.uuid != species_uuid,
                PersonalSpecies.deleted_at.is_(None),
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise BusinessError(ErrorCode.SPECIES_CONFLICT)
    for field, value in request.model_dump().items():
        setattr(species, field, value)
    await session.flush()
    return species


async def soft_delete_species(session: AsyncSession, user_id: int, species_uuid: UUID) -> None:
    """Soft-delete one personal species entry."""
    species = await _get_species(session, user_id, species_uuid)
    if species is None:
        raise BusinessError(ErrorCode.SPECIES_NOT_FOUND)
    species.deleted_at = utc_now()
    await session.flush()


async def create_gene(session: AsyncSession, user_id: int, request: GeneCreateRequest) -> PersonalGene:
    """Create one reusable personal gene entry."""
    gene = PersonalGene(user_id=user_id, **request.model_dump())
    session.add(gene)
    await session.flush()
    return gene


async def update_gene(session: AsyncSession, user_id: int, gene_uuid: UUID, request: GeneUpdateRequest) -> PersonalGene:
    """Update one active personal gene entry."""
    gene = await _get_gene(session, user_id, gene_uuid)
    if gene is None:
        raise BusinessError(ErrorCode.GENE_NOT_FOUND)
    for field, value in request.model_dump().items():
        setattr(gene, field, value)
    await session.flush()
    return gene


async def soft_delete_gene(session: AsyncSession, user_id: int, gene_uuid: UUID) -> None:
    """Soft-delete one personal gene entry."""
    gene = await _get_gene(session, user_id, gene_uuid)
    if gene is None:
        raise BusinessError(ErrorCode.GENE_NOT_FOUND)
    gene.deleted_at = utc_now()
    await session.flush()


async def create_tag(session: AsyncSession, user_id: int, request: TagCreateRequest) -> IdentificationTag:
    """Create one reusable personal identification tag."""
    tag = IdentificationTag(user_id=user_id, **request.model_dump())
    session.add(tag)
    await session.flush()
    return tag


async def update_tag(session: AsyncSession, user_id: int, tag_uuid: UUID, request: TagUpdateRequest) -> IdentificationTag:
    """Update one active personal identification tag."""
    tag = await _get_tag(session, user_id, tag_uuid)
    if tag is None:
        raise BusinessError(ErrorCode.IDENTIFICATION_TAG_NOT_FOUND)
    tag.name = request.name
    await session.flush()
    return tag


async def soft_delete_tag(session: AsyncSession, user_id: int, tag_uuid: UUID) -> None:
    """Soft-delete one personal identification tag."""
    tag = await _get_tag(session, user_id, tag_uuid)
    if tag is None:
        raise BusinessError(ErrorCode.IDENTIFICATION_TAG_NOT_FOUND)
    tag.deleted_at = utc_now()
    await session.flush()
