from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.errors import BusinessError, ErrorCode
from ...core.security.dependencies import get_current_user
from ...infra.database import get_db_session
from ...models import Pet, User
from ...schemas.pets import (
    AssignmentResponse,
    GeneResponse,
    LifeStageResponse,
    OriginResponse,
    PetListResponse,
    PetResponse,
)
from ...selectors import get_pet_by_uuid


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


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


def serialize_pet_detail(pet: Pet) -> PetResponse:
    """Serialize a fully loaded pet and its historical records."""
    compact = serialize_pet_list(pet)
    return PetResponse(
        **compact.model_dump(),
        identification_note=pet.identification_note,
        owner_note=pet.owner_note,
        genes=[GeneResponse.model_validate(gene) for gene in pet.genes],
        origins=[
            OriginResponse(
                uuid=origin.uuid,
                origin_type=origin.origin_type,
                parent_role=origin.parent_role,
                parent_pet_uuid=origin.parent_pet.uuid if origin.parent_pet else None,
                breeder_name=origin.breeder_name,
                external_name=origin.external_name,
                genetic_note=origin.genetic_note,
                confidence=origin.confidence,
                note=origin.note,
            )
            for origin in pet.origins
        ],
        life_stages=[LifeStageResponse.model_validate(stage) for stage in pet.life_stages],
        management_assignments=[
            AssignmentResponse.model_validate(assignment) for assignment in pet.assignments
        ],
    )


async def get_pet_or_404(
    session: AsyncSession, user_id: int, pet_uuid: UUID, detail: bool = False
) -> Pet:
    """Load a user-owned pet or raise the public domain not-found error."""
    pet = await get_pet_by_uuid(session, user_id, pet_uuid, detail=detail)
    if pet is None:
        raise BusinessError(ErrorCode.PET_NOT_FOUND)
    return pet
