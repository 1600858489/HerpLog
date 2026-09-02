from fastapi import APIRouter, status
from uuid import UUID

from ...core.response import ResponseEnvelope, success_response
from ...models import ManagementUnit
from ...schemas.pets import (
    ManagementUnitCreateRequest,
    ManagementUnitResponse,
    ManagementUnitTypeCreateRequest,
    ManagementUnitTypeResponse,
    ManagementUnitTypeUpdateRequest,
    ManagementUnitUpdateRequest,
    PetListResponse,
)
from ...selectors import list_management_unit_members, list_management_unit_types, list_management_units
from ...services import (
    clear_and_delete_management_unit,
    create_management_unit,
    soft_delete_management_unit,
    create_management_unit_type,
    soft_delete_management_unit_type,
    update_management_unit,
    update_management_unit_type,
)
from .common import CurrentUser, DbSession, serialize_pet_list


management_router = APIRouter()


def serialize_management_unit(unit: ManagementUnit) -> ManagementUnitResponse:
    """Serialize a loaded management unit with its public type summary."""
    return ManagementUnitResponse(
        uuid=unit.uuid,
        unit_code=unit.unit_code,
        name=unit.name,
        type=ManagementUnitTypeResponse.model_validate(unit.unit_type),
    )


@management_router.get("/management-unit-types", response_model=ResponseEnvelope[list[ManagementUnitTypeResponse]])
async def list_management_unit_types_view(current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[list[ManagementUnitTypeResponse]]:
    """List visible system and personal management-unit types."""
    items = await list_management_unit_types(session, current_user.id)
    return success_response([ManagementUnitTypeResponse.model_validate(item) for item in items])


@management_router.post("/management-unit-types", response_model=ResponseEnvelope[ManagementUnitTypeResponse], status_code=status.HTTP_201_CREATED)
async def create_management_unit_type_view(request: ManagementUnitTypeCreateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[ManagementUnitTypeResponse]:
    """Create one personal management-unit type."""
    item = await create_management_unit_type(session, current_user.id, request)
    await session.commit()
    return success_response(ManagementUnitTypeResponse.model_validate(item))


@management_router.patch("/management-unit-types/{type_uuid}", response_model=ResponseEnvelope[ManagementUnitTypeResponse])
async def update_management_unit_type_view(type_uuid: UUID, request: ManagementUnitTypeUpdateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[ManagementUnitTypeResponse]:
    """Update one personal management-unit type."""
    item = await update_management_unit_type(session, current_user.id, type_uuid, request)
    await session.commit()
    return success_response(ManagementUnitTypeResponse.model_validate(item))


@management_router.delete("/management-unit-types/{type_uuid}", response_model=ResponseEnvelope[None])
async def delete_management_unit_type_view(type_uuid: UUID, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[None]:
    """Soft-delete one personal management-unit type."""
    await soft_delete_management_unit_type(session, current_user.id, type_uuid)
    await session.commit()
    return success_response()


@management_router.get("/management-units", response_model=ResponseEnvelope[list[ManagementUnitResponse]])
async def list_management_units_view(current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[list[ManagementUnitResponse]]:
    """List the authenticated user's management units."""
    items = await list_management_units(session, current_user.id)
    return success_response([serialize_management_unit(item) for item in items])


@management_router.post("/management-units", response_model=ResponseEnvelope[ManagementUnitResponse], status_code=status.HTTP_201_CREATED)
async def create_management_unit_view(request: ManagementUnitCreateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[ManagementUnitResponse]:
    """Create one flat management unit."""
    item = await create_management_unit(session, current_user.id, request)
    await session.commit()
    loaded = await list_management_units(session, current_user.id)
    return success_response(serialize_management_unit(next(unit for unit in loaded if unit.uuid == item.uuid)))


@management_router.patch("/management-units/{unit_uuid}", response_model=ResponseEnvelope[ManagementUnitResponse])
async def update_management_unit_view(unit_uuid: UUID, request: ManagementUnitUpdateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[ManagementUnitResponse]:
    """Update one flat management unit."""
    await update_management_unit(session, current_user.id, unit_uuid, request)
    await session.commit()
    loaded = await list_management_units(session, current_user.id)
    return success_response(serialize_management_unit(next(unit for unit in loaded if unit.uuid == unit_uuid)))


@management_router.delete("/management-units/{unit_uuid}", response_model=ResponseEnvelope[None])
async def delete_management_unit_view(unit_uuid: UUID, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[None]:
    """Soft-delete one unassigned management unit."""
    await soft_delete_management_unit(session, current_user.id, unit_uuid)
    await session.commit()
    return success_response()


@management_router.get("/management-units/{unit_uuid}/members", response_model=ResponseEnvelope[list[PetListResponse]])
async def list_management_unit_members_view(unit_uuid: UUID, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[list[PetListResponse]]:
    """List pets currently assigned to one management unit."""
    items = await list_management_unit_members(session, current_user.id, unit_uuid)
    return success_response([serialize_pet_list(item) for item in items])


@management_router.post("/management-units/{unit_uuid}/clear-and-delete", response_model=ResponseEnvelope[None])
async def clear_delete_management_unit_view(unit_uuid: UUID, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[None]:
    """Clear active assignments and soft-delete one management unit."""
    await clear_and_delete_management_unit(session, current_user.id, unit_uuid)
    await session.commit()
    return success_response()
