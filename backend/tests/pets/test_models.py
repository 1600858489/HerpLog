from app.models import (
    Base,

    IdentificationTag,
    ManagementUnit,
    ManagementUnitType,
    PersonalGene,
    PersonalSpecies,
    Pet,
    PetLifeStage,
    User,
)


async def test_pet_domain_models_support_optional_classification_and_unnamed_pets(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        species = PersonalSpecies(user_id=user.id, common_name="豹纹守宫")
        session.add(species)
        await session.flush()
        pet = Pet(user_id=user.id, species_id=species.id, pet_code="PET-001", sex="unknown")
        session.add(pet)
        await session.commit()
        await session.refresh(pet)
        assert pet.name is None
        assert pet.pet_code == "PET-001"
        assert pet.uuid


async def test_management_unit_type_and_history_models_have_relationships(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        user = User(username="keeper", password_hash="hashed")
        session.add(user)
        await session.flush()
        species = PersonalSpecies(user_id=user.id, common_name="乌龟")
        unit_type = ManagementUnitType(user_id=user.id, name="生态缸", is_system=False)
        session.add_all([species, unit_type])
        await session.flush()
        unit = ManagementUnit(user_id=user.id, type_id=unit_type.id, unit_code="TANK-001")
        pet = Pet(user_id=user.id, species_id=species.id, pet_code="PET-001", sex="unknown")
        tag = IdentificationTag(user_id=user.id, name="背甲花纹")
        gene = PersonalGene(user_id=user.id, name="Albino")
        session.add_all([unit, pet, tag, gene])
        await session.flush()
        session.add(PetLifeStage(pet_id=pet.id, stage="幼体", started_at=pet.created_at))
        await session.commit()
        assert unit.uuid
        assert tag.uuid
        assert gene.uuid
