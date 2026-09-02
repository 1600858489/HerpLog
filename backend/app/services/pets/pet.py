from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...models import (
    IdentificationTag,
    PersonalGene,
    Pet,
    PetGene,
    PetIdentificationTag,
    PetLifeStage,
    PetManagementAssignment,
    PetOrigin,
)
from ...schemas.pets import PetCreateRequest, PetUpdateRequest
from ...selectors import get_gene_by_uuid, get_pet_by_uuid, get_species_by_uuid, get_tag_by_uuid
from ...utils.datetime import utc_now


async def _generate_pet_code(session: AsyncSession, user_id: int) -> str:
    """Generate the next readable pet code in one user's namespace."""
    result = await session.execute(
        select(Pet.pet_code)
        .where(Pet.user_id == user_id)
        .order_by(Pet.id.desc())
        .limit(1)
    )
    latest_code = result.scalar_one_or_none()
    next_number = 1
    if latest_code and latest_code.startswith("PET-") and latest_code[4:].isdigit():
        next_number = int(latest_code[4:]) + 1
    return f"PET-{next_number:03d}"


async def _validate_associations(
    session: AsyncSession, user_id: int, request: PetCreateRequest
) -> tuple[list[PersonalGene], list[IdentificationTag]]:
    """Validate all optional classification references in a pet request."""
    genes: list[PersonalGene] = []
    for gene_uuid in request.gene_uuids:
        gene = await get_gene_by_uuid(session, user_id, gene_uuid)
        if gene is None:
            raise BusinessError(ErrorCode.GENE_NOT_FOUND)
        genes.append(gene)

    tags: list[IdentificationTag] = []
    for tag_uuid in request.tag_uuids:
        tag = await get_tag_by_uuid(session, user_id, tag_uuid)
        if tag is None:
            raise BusinessError(ErrorCode.IDENTIFICATION_TAG_NOT_FOUND)
        tags.append(tag)
    return genes, tags


async def create_pet(session: AsyncSession, user_id: int, request: PetCreateRequest) -> Pet:
    """Create one user-owned pet with optional reusable classifications."""
    species = await get_species_by_uuid(session, user_id, request.species_uuid)
    if species is None:
        raise BusinessError(ErrorCode.SPECIES_NOT_FOUND)
    genes, tags = await _validate_associations(session, user_id, request)
    pet_code = request.pet_code or await _generate_pet_code(session, user_id)
    if await session.scalar(
        select(Pet.id).where(
            Pet.user_id == user_id,
            Pet.pet_code == pet_code,
            Pet.deleted_at.is_(None),
        )
    ):
        raise BusinessError(ErrorCode.PET_CONFLICT)

    pet = Pet(
        user_id=user_id,
        species_id=species.id,
        pet_code=pet_code,
        sex=request.sex,
        name=request.name,
        identification_note=request.identification_note,
        owner_note=request.owner_note,
    )
    session.add(pet)
    await session.flush()
    for gene in genes:
        session.add(PetGene(pet_id=pet.id, gene_id=gene.id))
    for tag in tags:
        session.add(PetIdentificationTag(pet_id=pet.id, tag_id=tag.id))
    await session.flush()
    return pet


async def update_pet(
    session: AsyncSession, user_id: int, pet_uuid: UUID, request: PetUpdateRequest
) -> Pet:
    """Update editable base fields for one user-owned pet."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    if request.species_uuid is not None:
        species = await get_species_by_uuid(session, user_id, request.species_uuid)
        if species is None:
            raise BusinessError(ErrorCode.SPECIES_NOT_FOUND)
        pet.species_id = species.id
    if request.pet_code is not None and request.pet_code != pet.pet_code:
        duplicate = await session.scalar(
            select(Pet.id).where(
                Pet.user_id == user_id,
                Pet.pet_code == request.pet_code,
                Pet.uuid != pet_uuid,
                Pet.deleted_at.is_(None),
            )
        )
        if duplicate is not None:
            raise BusinessError(ErrorCode.PET_CONFLICT)
        pet.pet_code = request.pet_code
    for field in ("sex", "name", "identification_note", "owner_note"):
        value = getattr(request, field)
        if value is not None:
            setattr(pet, field, value)
    await session.flush()
    return pet


async def soft_delete_pet(session: AsyncSession, user_id: int, pet_uuid: UUID) -> None:
    """Soft-delete a pet and all of its historical relationship records."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    deleted_at = utc_now()
    pet.deleted_at = deleted_at
    for model in (PetManagementAssignment, PetLifeStage, PetOrigin, PetGene, PetIdentificationTag):
        result = await session.execute(
            select(model).where(model.pet_id == pet.id, model.deleted_at.is_(None))
        )
        for record in result.scalars():
            record.deleted_at = deleted_at
    await session.flush()


__all__ = ["create_pet", "soft_delete_pet", "update_pet"]
