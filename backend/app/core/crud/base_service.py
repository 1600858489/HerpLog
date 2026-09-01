from datetime import datetime
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from ...utils.datetime import utc_now
from .base_selector import BaseSelector

ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")


class BaseCRUDService(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    """Provide explicit extension points for ordinary CRUD lifecycle operations."""

    def __init__(self, model: type[ModelT], selector: BaseSelector[ModelT]) -> None:
        self.model = model
        self.selector = selector

    def build_model(self, user_id: int, request: CreateSchemaT) -> ModelT:
        """Build a model from a validated request; business services override this."""
        raise NotImplementedError

    def apply_update(self, model: ModelT, request: UpdateSchemaT) -> None:
        """Apply validated update fields; business services override this."""
        raise NotImplementedError

    async def create(self, session: AsyncSession, user_id: int, request: CreateSchemaT) -> ModelT:
        """Create and flush one user-owned model without committing a larger workflow."""
        model = self.build_model(user_id, request)
        session.add(model)
        await session.flush()
        return model

    async def update(
        self,
        session: AsyncSession,
        user_id: int,
        resource_uuid,
        request: UpdateSchemaT,
    ) -> ModelT:
        """Update one resource selected within the configured user scope."""
        model = await self.selector.get_by_uuid(session, user_id, resource_uuid)
        if model is None:
            raise LookupError("resource not found")
        self.apply_update(model, request)
        await session.flush()
        return model

    async def soft_delete(self, session: AsyncSession, user_id: int, resource_uuid) -> None:
        """Mark one user-owned resource deleted without hard deletion."""
        model = await self.selector.get_by_uuid(session, user_id, resource_uuid)
        if model is None:
            raise LookupError("resource not found")
        model.deleted_at = utc_now()  # type: ignore[attr-defined]
        await session.flush()
