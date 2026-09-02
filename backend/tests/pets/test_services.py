from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.errors import BusinessError, ErrorCode
from app.models import (
    ManagementUnit,
    ManagementUnitType,
    PersonalSpecies,
    Pet,
    PetManagementAssignment,
    User,
)
from app.schemas.pets import AssignmentMoveRequest, PetCreateRequest
from app.services.pets.lifecycle import move_pet
from app.services.pets.pet import create_pet, soft_delete_pet
from app.utils.datetime import utc_now


async def test_create_pet_allows_no_name_and_no_management_unit(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        species = PersonalSpecies(user_id=user.id, common_name="龟")
        session.add(species)
        await session.flush()
        pet = await create_pet(session, user.id, PetCreateRequest(species_uuid=species.uuid))
        assert pet.name is None
        assert pet.pet_code


async def test_pet_delete_soft_deletes_history(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        species = PersonalSpecies(user_id=user.id, common_name="龟")
        unit_type = ManagementUnitType(user_id=user.id, name="龟池", is_system=False)
        session.add_all([species, unit_type])
        await session.flush()
        pet = await create_pet(session, user.id, PetCreateRequest(species_uuid=species.uuid))
        unit = ManagementUnit(user_id=user.id, type_id=unit_type.id, unit_code="POOL-001")
        session.add(unit)
        await session.flush()
        assignment = PetManagementAssignment(
            pet_id=pet.id,
            management_unit_id=unit.id,
            started_at=utc_now() - timedelta(days=1),
        )
        session.add(assignment)
        await session.commit()
        await soft_delete_pet(session, user.id, pet.uuid)
        assert pet.deleted_at is not None
        assert assignment.deleted_at is not None


async def test_overlapping_management_assignment_is_rejected(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        species = PersonalSpecies(user_id=user.id, common_name="龟")
        first_type = ManagementUnitType(user_id=user.id, name="龟池一", is_system=False)
        second_type = ManagementUnitType(user_id=user.id, name="龟池二", is_system=False)
        session.add_all([species, first_type, second_type])
        await session.flush()
        pet = await create_pet(session, user.id, PetCreateRequest(species_uuid=species.uuid))
        first_unit = ManagementUnit(user_id=user.id, type_id=first_type.id, unit_code="POOL-001")
        second_unit = ManagementUnit(user_id=user.id, type_id=second_type.id, unit_code="POOL-002")
        session.add_all([first_unit, second_unit])
        await session.flush()
        session.add(
            PetManagementAssignment(
                pet_id=pet.id,
                management_unit_id=first_unit.id,
                started_at=utc_now() - timedelta(days=1),
            )
        )
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await move_pet(
                session,
                user.id,
                pet.uuid,
                AssignmentMoveRequest(management_unit_uuid=first_unit.uuid, started_at=utc_now()),
            )
        assert error.value.error_code == ErrorCode.ORIGIN_OR_ASSIGNMENT_INVALID_STATE
