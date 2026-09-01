import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest


def test_register_rejects_request_without_any_identity() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(password="strong-password")


def test_register_derives_username_from_phone_or_email() -> None:
    request = RegisterRequest(phone=" 13800138000 ", password="strong-password")
    assert request.phone == "13800138000"
    assert request.username == "13800138000"


def test_register_normalizes_email_and_forbids_internal_ids() -> None:
    request = RegisterRequest(email=" Keeper@Example.COM ", password="strong-password")
    assert request.email == "keeper@example.com"
    assert request.username == "keeper@example.com"
    with pytest.raises(ValidationError):
        RegisterRequest(username="keeper", password="strong-password", id=1)


def test_login_requires_identifier_and_password() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(identifier="keeper", password="short")
