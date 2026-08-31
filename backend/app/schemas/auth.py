from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from backend.app.schemas.base import BaseRequestSchema


class RegisterRequest(BaseRequestSchema):
    """Validate account registration identity and password input."""

    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=32)
    email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", "phone", mode="before")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        identities = [self.username, self.phone, self.email]
        if not any(identities):
            raise ValueError("at least one registration identity is required")
        if self.username is None and self.phone is not None and self.email is not None:
            raise ValueError("phone and email cannot both derive username")
        if self.username is None:
            object.__setattr__(self, "username", self.phone or str(self.email))
        return self


class LoginRequest(BaseRequestSchema):
    """Validate a login identifier and password."""

    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    device_info: str | None = Field(default=None, max_length=255)

    @field_validator("identifier", "device_info", mode="before")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class RefreshRequest(BaseRequestSchema):
    """Validate an opaque refresh token submitted for rotation."""

    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseRequestSchema):
    """Validate an opaque refresh token submitted for revocation."""

    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    """Serialize public account fields without internal database identifiers."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    uuid: UUID
    username: str
    phone: str | None
    email: str | None


class AuthResponse(BaseRequestSchema):
    """Serialize issued access and refresh credentials with the public user."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "LogoutRequest",
    "UserResponse",
    "AuthResponse",
]
