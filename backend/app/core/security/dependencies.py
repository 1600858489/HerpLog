from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import BusinessError, ErrorCode
from .jwt import decode_access_token
from ...infra.database import get_db_session
from ...models import User
from ...selectors import get_user_by_uuid


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Resolve the active user identified by a valid public access-token UUID."""
    if credentials is None:
        raise BusinessError(ErrorCode.UNAUTHORIZED)
    payload = decode_access_token(credentials.credentials)
    try:
        user_uuid = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise BusinessError(ErrorCode.INVALID_ACCESS_TOKEN) from exc
    user = await get_user_by_uuid(session, user_uuid)
    if user is None:
        raise BusinessError(ErrorCode.UNAUTHORIZED)
    return user


__all__ = ["bearer_scheme", "get_current_user"]
