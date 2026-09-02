from datetime import timedelta

import pytest

from app.core.errors import BusinessError, ErrorCode
from app.models import (
    ManagementUnit,
    ManagementUnitType,
    PersonalSpecies,
    Pet,
    PetManagementAssignment,
    User,
)
from app.schemas.pets import ManagementUnitTypeCreateRequest, ManagementUnitTypeUpdateRequest
from app.services.pets.management import (
    clear_and_delete_management_unit,
    create_management_unit_type,
    update_management_unit_type,
)


async def test_custom_management_unit_type_cannot_duplicate_system_name(async_session_factory) -> None:
    async with async_session_factory() as session:
        system_type = ManagementUnitType(name="生态缸", is_system=True, user_id=None)
        session.add(system_type)
        await session.flush()
        with pytest.raises(BusinessError) as error:
            await create_management_unit_type(
                session, 1, ManagementUnitTypeCreateRequest(name="生态缸")
            )
        assert error.value.error_code == ErrorCode.MANAGEMENT_UNIT_TYPE_CONFLICT


from app.utils.datetime import utc_now


async def test_system_management_unit_type_cannot_be_modified(async_session_factory) -> None:
    async with async_session_factory() as session:
        system_type = ManagementUnitType(name="生态缸", is_system=True, user_id=None)
        session.add(system_type)
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await update_management_unit_type(
                session, 1, system_type.uuid, ManagementUnitTypeUpdateRequest(name="修改")
            )
        assert error.value.error_code == ErrorCode.MANAGEMENT_UNIT_TYPE_FORBIDDEN


async def test_clear_and_delete_leaves_pets_unassigned(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        species = PersonalSpecies(user_id=user.id, common_name="龟")
        unit_type = ManagementUnitType(user_id=user.id, name="龟池", is_system=False)
        session.add_all([species, unit_type])
        await session.flush()
        unit = ManagementUnit(user_id=user.id, type_id=unit_type.id, unit_code="POOL-001")
        pet = Pet(user_id=user.id, species_id=species.id, pet_code="PET-001", sex="unknown")
        session.add_all([unit, pet])
        await session.flush()
        assignment = PetManagementAssignment(
            pet_id=pet.id,
            management_unit_id=unit.id,
            started_at=utc_now() - timedelta(days=1),
        )
        session.add(assignment)
        await session.commit()
        await clear_and_delete_management_unit(session, user.id, unit.uuid)
        assert pet.deleted_at is None
        assert assignment.ended_at is not None
        assert unit.deleted_at is not None
