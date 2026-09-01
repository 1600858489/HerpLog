from app.core.crud import BaseCRUDService, BaseSelector


def test_crud_abstractions_define_explicit_extension_points() -> None:
    assert BaseSelector.__parameters__
    assert BaseCRUDService.__parameters__
    assert hasattr(BaseSelector, "get_by_uuid")
    assert hasattr(BaseSelector, "list_paginated")
    assert hasattr(BaseCRUDService, "create")
    assert hasattr(BaseCRUDService, "update")
    assert hasattr(BaseCRUDService, "soft_delete")
