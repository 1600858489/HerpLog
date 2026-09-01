from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import RefreshToken, User


async def get_user_by_identifier(session: AsyncSession, identifier: str) -> User | None:
    """Find an active user by username, phone, or email."""
    result = await session.execute(
        select(User).where(
            User.deleted_at.is_(None),
            or_(User.username == identifier, User.phone == identifier, User.email == identifier),
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_uuid(session: AsyncSession, user_uuid: UUID) -> User | None:
    """Find an active user by public UUID."""
    result = await session.execute(
        select(User).where(User.uuid == user_uuid, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_refresh_token_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    """Find one refresh-token credential and explicitly load its user."""
    result = await session.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.deleted_at.is_(None),
        )
        .options(selectinload(RefreshToken.user))
    )
    return result.scalar_one_or_none()


__all__ = ["get_user_by_identifier", "get_user_by_uuid", "get_refresh_token_by_hash"]
