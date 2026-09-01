from collections.abc import Sequence
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from ..pagination import PaginationParams

ModelT = TypeVar("ModelT")


class BaseSelector(Generic[ModelT]):
    """Provide explicit user-scoped UUID and pagination query primitives."""

    def __init__(
        self,
        model: type[ModelT],
        owner_column: InstrumentedAttribute[int],
        load_options: Sequence[object] = (),
    ) -> None:
        self.model = model
        self.owner_column = owner_column
        self.load_options = tuple(load_options)

    def base_query(self, user_id: int) -> Select[tuple[ModelT]]:
        """Build an active user-scoped query for the configured model."""
        query = select(self.model).where(
            self.owner_column == user_id,
            self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
        )
        return query.options(*self.load_options)

    async def get_by_uuid(
        self, session: AsyncSession, user_id: int, resource_uuid: UUID
    ) -> ModelT | None:
        """Return one active resource owned by the specified user."""
        result = await session.execute(
            self.base_query(user_id).where(self.model.uuid == resource_uuid)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, session: AsyncSession, user_id: int, params: PaginationParams
    ) -> tuple[list[ModelT], int]:
        """Return one page and total count for the configured user scope."""
        result = await session.execute(
            self.base_query(user_id)
            .order_by(self.model.created_at.desc(), self.model.id.desc())  # type: ignore[attr-defined]
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )
        count_result = await session.execute(
            select(func.count()).select_from(self.base_query(user_id).subquery())
        )
        return list(result.scalars().all()), count_result.scalar_one()
