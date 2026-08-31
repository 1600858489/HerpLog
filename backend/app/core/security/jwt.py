from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from backend.app.core.config import get_settings
from backend.app.core.errors import BusinessError, ErrorCode


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed short-lived access token for a public user UUID."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "type": "access", "iat": now, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate an access token and return its claims without leaking decoder errors."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise BusinessError(ErrorCode.INVALID_ACCESS_TOKEN) from exc
    if payload.get("type") != "access" or not isinstance(payload.get("sub"), str):
        raise BusinessError(ErrorCode.INVALID_ACCESS_TOKEN)
    return payload
