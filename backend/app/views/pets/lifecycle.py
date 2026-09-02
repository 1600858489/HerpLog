from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...core.pagination import PaginationData, PaginationParams, build_pagination
from ...core.response import ResponseEnvelope, success_response
from ...schemas.pets import (
    AssignmentCreateRequest,
    AssignmentEndRequest,
    AssignmentMoveRequest,
    AssignmentResponse,
    LifeStageCreateRequest,
    LifeStageResponse,
    LifeStageUpdateRequest,
    OriginCreateRequest,
    OriginResponse,
    OriginUpdateRequest,
)
from ...selectors import (
    get_pet_assignment_by_uuid,
    get_pet_origin_by_uuid,
    list_pet_assignments,
    list_pet_life_stages,
    list_pet_origins,
)
from ...services import (
    create_assignment,
    create_life_stage,
    create_origin,
    end_life_stage,
    move_pet,
    remove_pet_from_management_unit,
    soft_delete_origin,
    update_life_stage,
    update_origin,
)
from .common import CurrentUser, DbSession


lifecycle_router = APIRouter()
PaginationQuery = Annotated[PaginationParams, Depends()]


@lifecycle_router.get("/pets/{pet_uuid}/management-assignments", response_model=ResponseEnvelope[PaginationData[AssignmentResponse]])
async def list_assignments_view(pet_uuid: UUID, current_user: CurrentUser, session: DbSession, pagination: PaginationQuery) -> ResponseEnvelope[PaginationData[AssignmentResponse]]:
    """List assignment history for one pet."""
    items, total = await list_pet_assignments(session, current_user.id, pet_uuid, pagination)
    return success_response(build_pagination([AssignmentResponse.model_validate(item) for item in items], total, pagination))


@lifecycle_router.post("/pets/{pet_uuid}/management-assignments", response_model=ResponseEnvelope[AssignmentResponse], status_code=status.HTTP_201_CREATED)
async def create_assignment_view(pet_uuid: UUID, request: AssignmentCreateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[AssignmentResponse]:
    """Create an initial assignment for one pet."""
    item = await create_assignment(session, current_user.id, pet_uuid, request)
    await session.commit()
    assignment = await get_pet_assignment_by_uuid(session, current_user.id, pet_uuid, item.uuid)
    if assignment is None:
        raise RuntimeError("Created assignment was not found")
    return success_response(AssignmentResponse.model_validate(assignment))


@lifecycle_router.post("/pets/{pet_uuid}/management-assignments/move", response_model=ResponseEnvelope[AssignmentResponse], status_code=status.HTTP_201_CREATED)
async def move_pet_view(pet_uuid: UUID, request: AssignmentMoveRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[AssignmentResponse]:
    """Move one pet to another management unit."""
    item = await move_pet(session, current_user.id, pet_uuid, request)
    await session.commit()
    assignment = await get_pet_assignment_by_uuid(session, current_user.id, pet_uuid, item.uuid)
    if assignment is None:
        raise RuntimeError("Created assignment was not found")
    return success_response(AssignmentResponse.model_validate(assignment))


@lifecycle_router.post("/pets/{pet_uuid}/management-assignments/remove", response_model=ResponseEnvelope[None])
async def remove_assignment_view(pet_uuid: UUID, request: AssignmentEndRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[None]:
    """End the current assignment while preserving the pet."""
    await remove_pet_from_management_unit(session, current_user.id, pet_uuid, request.ended_at)
    await session.commit()
    return success_response()


@lifecycle_router.get("/pets/{pet_uuid}/life-stages", response_model=ResponseEnvelope[PaginationData[LifeStageResponse]])
async def list_life_stages_view(pet_uuid: UUID, current_user: CurrentUser, session: DbSession, pagination: PaginationQuery) -> ResponseEnvelope[PaginationData[LifeStageResponse]]:
    """List life-stage history for one pet."""
    items, total = await list_pet_life_stages(session, current_user.id, pet_uuid, pagination)
    return success_response(build_pagination([LifeStageResponse.model_validate(item) for item in items], total, pagination))


@lifecycle_router.post("/pets/{pet_uuid}/life-stages", response_model=ResponseEnvelope[LifeStageResponse], status_code=status.HTTP_201_CREATED)
async def create_life_stage_view(pet_uuid: UUID, request: LifeStageCreateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[LifeStageResponse]:
    """Create a life-stage interval for one pet."""
    item = await create_life_stage(session, current_user.id, pet_uuid, request)
    await session.commit()
    return success_response(LifeStageResponse.model_validate(item))


@lifecycle_router.patch("/pets/{pet_uuid}/life-stages/{stage_uuid}", response_model=ResponseEnvelope[LifeStageResponse])
async def update_life_stage_view(pet_uuid: UUID, stage_uuid: UUID, request: LifeStageUpdateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[LifeStageResponse]:
    """Update one life-stage record."""
    item = await update_life_stage(session, current_user.id, pet_uuid, stage_uuid, request)
    await session.commit()
    return success_response(LifeStageResponse.model_validate(item))


@lifecycle_router.post("/pets/{pet_uuid}/life-stages/{stage_uuid}", response_model=ResponseEnvelope[LifeStageResponse])
async def end_life_stage_view(pet_uuid: UUID, stage_uuid: UUID, request: AssignmentEndRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[LifeStageResponse]:
    """End one active life-stage interval."""
    item = await end_life_stage(session, current_user.id, pet_uuid, stage_uuid, request.ended_at)
    await session.commit()
    return success_response(LifeStageResponse.model_validate(item))


@lifecycle_router.get("/pets/{pet_uuid}/origins", response_model=ResponseEnvelope[PaginationData[OriginResponse]])
async def list_origins_view(pet_uuid: UUID, current_user: CurrentUser, session: DbSession, pagination: PaginationQuery) -> ResponseEnvelope[PaginationData[OriginResponse]]:
    """List source history for one pet."""
    items, total = await list_pet_origins(session, current_user.id, pet_uuid, pagination)
    return success_response(build_pagination([OriginResponse.model_validate(item) for item in items], total, pagination))


@lifecycle_router.post("/pets/{pet_uuid}/origins", response_model=ResponseEnvelope[OriginResponse], status_code=status.HTTP_201_CREATED)
async def create_origin_view(pet_uuid: UUID, request: OriginCreateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[OriginResponse]:
    """Create one source record for a pet."""
    item = await create_origin(session, current_user.id, pet_uuid, request)
    await session.commit()
    return success_response(OriginResponse(
        uuid=item.uuid, origin_type=item.origin_type, parent_role=item.parent_role,
        parent_pet_uuid=request.parent_pet_uuid, breeder_name=item.breeder_name,
        external_name=item.external_name, genetic_note=item.genetic_note,
        confidence=item.confidence, note=item.note,
    ))


@lifecycle_router.patch("/pets/{pet_uuid}/origins/{origin_uuid}", response_model=ResponseEnvelope[OriginResponse])
async def update_origin_view(pet_uuid: UUID, origin_uuid: UUID, request: OriginUpdateRequest, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[OriginResponse]:
    """Update one source record for a pet."""
    await update_origin(session, current_user.id, pet_uuid, origin_uuid, request)
    await session.commit()
    origin = await get_pet_origin_by_uuid(session, current_user.id, pet_uuid, origin_uuid)
    if origin is None:
        raise RuntimeError("Updated origin was not found")
    return success_response(OriginResponse(
        uuid=origin.uuid, origin_type=origin.origin_type, parent_role=origin.parent_role,
        parent_pet_uuid=origin.parent_pet.uuid if origin.parent_pet else None,
        breeder_name=origin.breeder_name, external_name=origin.external_name,
        genetic_note=origin.genetic_note, confidence=origin.confidence, note=origin.note,
    ))


@lifecycle_router.delete("/pets/{pet_uuid}/origins/{origin_uuid}", response_model=ResponseEnvelope[None])
async def delete_origin_view(pet_uuid: UUID, origin_uuid: UUID, current_user: CurrentUser, session: DbSession) -> ResponseEnvelope[None]:
    """Soft-delete one source record for a pet."""
    await soft_delete_origin(session, current_user.id, pet_uuid, origin_uuid)
    await session.commit()
    return success_response()
