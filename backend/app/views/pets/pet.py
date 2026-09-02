from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...core.errors import BusinessError, ErrorCode
from ...core.pagination import PaginationData, PaginationParams, build_pagination
from ...core.response import ResponseEnvelope, success_response
from ...schemas.pets import PetCreateRequest, PetListFilters, PetListResponse, PetResponse, PetUpdateRequest
from ...selectors import get_pet_by_uuid, list_pets
from ...services import create_pet, soft_delete_pet, update_pet
from .common import CurrentUser, DbSession, get_pet_or_404, serialize_pet_detail, serialize_pet_list


pet_router = APIRouter()


@pet_router.post("/pets", response_model=ResponseEnvelope[PetListResponse], status_code=status.HTTP_201_CREATED)
async def create_pet_view(
    request: PetCreateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[PetListResponse]:
    """Create a private pet record."""
    pet = await create_pet(session, current_user.id, request)
    await session.commit()
    return success_response(serialize_pet_list(await get_pet_or_404(session, current_user.id, pet.uuid)))


@pet_router.get("/pets", response_model=ResponseEnvelope[PaginationData[PetListResponse]])
async def list_pet_view(
    current_user: CurrentUser,
    session: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[PetListFilters, Depends()],
) -> ResponseEnvelope[PaginationData[PetListResponse]]:
    """Return a paginated compact list of the user's pets."""
    pets, total = await list_pets(session, current_user.id, pagination, filters)
    items = [serialize_pet_list(pet) for pet in pets]
    return success_response(build_pagination(items, total, pagination))


@pet_router.patch("/pets/{pet_uuid}", response_model=ResponseEnvelope[PetListResponse])
async def update_pet_view(
    pet_uuid: UUID, request: PetUpdateRequest, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[PetListResponse]:
    """Update editable base fields for one pet."""
    await update_pet(session, current_user.id, pet_uuid, request)
    await session.commit()
    return success_response(serialize_pet_list(await get_pet_or_404(session, current_user.id, pet_uuid)))


@pet_router.delete("/pets/{pet_uuid}", response_model=ResponseEnvelope[None])
async def delete_pet_view(
    pet_uuid: UUID, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[None]:
    """Soft-delete one pet and its historical relationship records."""
    await soft_delete_pet(session, current_user.id, pet_uuid)
    await session.commit()
    return success_response()


@pet_router.get("/pets/{pet_uuid}", response_model=ResponseEnvelope[PetResponse])
async def get_pet_view(
    pet_uuid: UUID, current_user: CurrentUser, session: DbSession
) -> ResponseEnvelope[PetResponse]:
    """Return one private pet record with its histories."""
    pet = await get_pet_or_404(session, current_user.id, pet_uuid, detail=True)
    return success_response(serialize_pet_detail(pet))


__all__ = ["pet_router"]
