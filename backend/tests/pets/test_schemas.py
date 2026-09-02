from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.pets import PetCreateRequest, SpeciesCreateRequest


def test_pet_create_requires_species_but_allows_unnamed_pet() -> None:
    request = PetCreateRequest(species_uuid=UUID("00000000-0000-0000-0000-000000000001"))
    assert request.name is None
    assert request.sex == "unknown"


def test_pet_request_forbids_internal_identifiers() -> None:
    with pytest.raises(ValidationError):
        PetCreateRequest(species_uuid="00000000-0000-0000-0000-000000000001", id=1)
    with pytest.raises(ValidationError):
        PetCreateRequest(species_uuid="00000000-0000-0000-0000-000000000001", user_id=1)


def test_species_scientific_fields_are_optional() -> None:
    request = SpeciesCreateRequest(common_name="豹纹守宫")
    assert request.scientific_name is None
    assert request.kingdom is None
