from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...core.pagination import PaginationData, PaginationParams, build_pagination
from ...core.response import ResponseEnvelope, success_response
from ...core.security.dependencies import get_current_user
from ...infra.database import get_db_session
from ...models import Pet, User
from ...schemas.pets import (
    PetCreateRequest,
    PetListFilters,
    PetListResponse,
    SpeciesCreateRequest,
    SpeciesResponse,
)
from ...selectors import get_pet_by_uuid, list_pets
from ...services import create_pet, create_species


pet_router = APIRouter()


def serialize_pet_list(pet: Pet) -> PetListResponse:
    """Serialize a loaded pet into the compact list response."""
    current_assignment = next(
        (assignment for assignment in pet.assignments if assignment.ended_at is None), None
    )
    unit = current_assignment.management_unit if current_assignment else None
    return PetListResponse(
        uuid=pet.uuid,
        pet_code=pet.pet_code,
        name=pet.name,
        species={"uuid": pet.species.uuid, "common_name": pet.species.common_name},
        sex=pet.sex,
        current_management_unit=(
            {"uuid": unit.uuid, "name": unit.name, "unit_code": unit.unit_code}
            if unit
            else None
        ),
        identification_tags=[
            {"uuid": tag.uuid, "name": tag.name} for tag in pet.identification_tags
        ],
    )


@pet_router.post(
    "/species",
    response_model=ResponseEnvelope[SpeciesResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_species_view(
    request: SpeciesCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[SpeciesResponse]:
    """Create a private species record for the authenticated user."""
    species = await create_species(session, current_user.id, request)
    await session.commit()
    return success_response(SpeciesResponse.model_validate(species))


@pet_router.post(
    "/pets",
    response_model=ResponseEnvelope[PetListResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_pet_view(
    request: PetCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[PetListResponse]:
    """Create a private pet record for the authenticated user."""
    pet = await create_pet(session, current_user.id, request)
    await session.commit()
    loaded_pet = await get_pet_by_uuid(session, current_user.id, pet.uuid)
    if loaded_pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    return success_response(serialize_pet_list(loaded_pet))


@pet_router.get("/pets/{pet_uuid}", response_model=ResponseEnvelope[PetListResponse])
async def get_pet_view(
    pet_uuid: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[PetListResponse]:
    """Return one private pet record."""
    pet = await get_pet_by_uuid(session, current_user.id, pet_uuid)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    return success_response(serialize_pet_list(pet))


@pet_router.get("/pets", response_model=ResponseEnvelope[PaginationData[PetListResponse]])
async def list_pet_view(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[PetListFilters, Depends()],
) -> ResponseEnvelope[PaginationData[PetListResponse]]:
    """Return a paginated compact list of the user's pets."""
    pets, total = await list_pets(session, current_user.id, pagination, filters)
    items = [serialize_pet_list(pet) for pet in pets]
    return success_response(build_pagination(items, total, pagination))


__all__ = ["pet_router"]
