from datetime import timezone
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.core.errors import ErrorCode, get_error_metadata
from app.core.pagination import PaginationParams, build_pagination
from app.core.response import success_response
from app.utils.datetime import utc_now
from app.utils.string import normalize_optional_text
from app.utils.uuid import generate_uuid


def test_production_rejects_development_jwt_secret() -> None:
    settings = Settings(environment="production")
    with pytest.raises(ValueError):
        settings.validate_production_security()


def test_production_accepts_configured_jwt_secret() -> None:
    settings = Settings(environment="production", jwt_secret_key="a-real-production-secret")
    settings.validate_production_security()


async def test_database_url_can_be_overridden_with_postgres_asyncpg_url(monkeypatch) -> None:
    database_url = "postgresql+asyncpg://herplog:secret@localhost:5432/herplog"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()
    engine = create_async_engine(settings.database_url)

    assert settings.database_url == database_url
    assert engine.url.drivername == "postgresql+asyncpg"
    await engine.dispose()


def test_test_runner_is_configured() -> None:
    assert True


def test_generate_uuid_returns_uuid() -> None:
    assert isinstance(generate_uuid(), UUID)


def test_utc_now_is_timezone_aware() -> None:
    assert utc_now().tzinfo == timezone.utc


def test_normalize_optional_text_trims_and_converts_blank_to_none() -> None:
    assert normalize_optional_text("  gecko  ") == "gecko"
    assert normalize_optional_text("   ") is None
    assert normalize_optional_text(None) is None


def test_business_error_metadata_contains_http_status_and_message() -> None:
    metadata = get_error_metadata(ErrorCode.PET_NOT_FOUND)
    assert metadata.http_status == 404
    assert metadata.message


def test_response_envelope_contains_code_message_and_data() -> None:
    response = success_response({"uuid": "public-id"})
    assert response.code == 0
    assert response.message == "success"
    assert response.data == {"uuid": "public-id"}


def test_pagination_rejects_page_zero_and_page_size_over_limit() -> None:
    with pytest.raises(ValidationError):
        PaginationParams(page=0)
    with pytest.raises(ValidationError):
        PaginationParams(page_size=101)


def test_pagination_builds_total_pages() -> None:
    result = build_pagination(["a", "b"], total=7, params=PaginationParams(page=2, page_size=2))
    assert result.items == ["a", "b"]
    assert result.total == 7
    assert result.total_pages == 4


def test_request_schema_forbids_internal_identifiers() -> None:
    from app.schemas.base import BaseRequestSchema

    class ExampleRequest(BaseRequestSchema):
        name: str

    with pytest.raises(ValidationError):
        ExampleRequest(name="sample", id=1)
    with pytest.raises(ValidationError):
        ExampleRequest(name="sample", uuid="public-id")

