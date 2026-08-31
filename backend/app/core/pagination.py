from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, Field

from backend.app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


ItemT = TypeVar("ItemT")


class PaginationParams(BaseModel):
    """Validate one-based pagination query parameters for list endpoints."""

    page: int = Field(DEFAULT_PAGE, ge=1)
    page_size: int = Field(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)


class PaginationData(BaseModel, Generic[ItemT]):
    """Represent a paginated API result with stable metadata."""

    items: list[ItemT]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


def build_pagination(
    items: Sequence[ItemT], total: int, params: PaginationParams
) -> PaginationData[ItemT]:
    """Build pagination metadata from already queried items and total count."""
    return PaginationData(
        items=list(items),
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=ceil(total / params.page_size) if total else 0,
    )
