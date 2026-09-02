import pytest

from app.core.errors import BusinessError, ErrorCode
from app.schemas.pets import SpeciesCreateRequest
from app.services.pets.classification import create_species
from app.models import User


async def test_species_is_private_and_duplicate_name_is_rejected(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        first = await create_species(session, user.id, SpeciesCreateRequest(common_name="龟"))
        assert first.common_name == "龟"
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await create_species(session, user.id, SpeciesCreateRequest(common_name="龟"))
        assert error.value.error_code == ErrorCode.SPECIES_CONFLICT


async def test_different_users_can_have_same_species_name(async_session_factory) -> None:
    async with async_session_factory() as session:
        first_user = User(username="first", password_hash="hashed")
        second_user = User(username="second", password_hash="hashed")
        session.add_all([first_user, second_user])
        await session.flush()
        first = await create_species(session, first_user.id, SpeciesCreateRequest(common_name="龟"))
        second = await create_species(session, second_user.id, SpeciesCreateRequest(common_name="龟"))
        assert first.uuid != second.uuid
