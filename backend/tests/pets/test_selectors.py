from app.core.pagination import PaginationParams
from app.models import PersonalSpecies, Pet, User
from app.schemas.pets import PetListFilters
from app.selectors.pets import get_pet_by_uuid, list_pets


async def test_pet_selector_cannot_return_another_users_pet(async_session_factory) -> None:
    async with async_session_factory() as session:
        owner = User(username="owner", password_hash="hashed")
        other = User(username="other", password_hash="hashed")
        session.add_all([owner, other])
        await session.flush()
        species = PersonalSpecies(user_id=owner.id, common_name="龟")
        session.add(species)
        await session.flush()
        pet = Pet(user_id=owner.id, species_id=species.id, pet_code="PET-001", sex="unknown")
        session.add(pet)
        await session.commit()
        assert await get_pet_by_uuid(session, other.id, pet.uuid) is None


async def test_pet_list_returns_pagination_count(async_session_factory) -> None:
    async with async_session_factory() as session:
        owner = User(username="owner", password_hash="hashed")
        session.add(owner)
        await session.flush()
        species = PersonalSpecies(user_id=owner.id, common_name="龟")
        session.add(species)
        await session.flush()
        session.add_all(
            [Pet(user_id=owner.id, species_id=species.id, pet_code=f"PET-{index:03d}", sex="unknown") for index in range(3)]
        )
        await session.commit()
        items, total = await list_pets(
            session, owner.id, PaginationParams(page=1, page_size=2), PetListFilters()
        )
        assert len(items) == 2
        assert total == 3
