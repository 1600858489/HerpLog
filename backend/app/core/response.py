from typing import Generic, TypeVar

from pydantic import BaseModel

from .errors import ErrorCode, get_error_metadata


DataT = TypeVar("DataT")


class ResponseEnvelope(BaseModel, Generic[DataT]):
    """Common API response wrapper shared by successful and failed requests."""

    code: int
    message: str
    data: DataT | None = None


def success_response(data: DataT | None = None) -> ResponseEnvelope[DataT]:
    """Build a successful response envelope."""
    return ResponseEnvelope(code=int(ErrorCode.SUCCESS), message="success", data=data)


def error_response(error_code: ErrorCode) -> ResponseEnvelope[None]:
    """Build a safe error envelope from centralized error metadata."""
    metadata = get_error_metadata(error_code)
    return ResponseEnvelope(code=int(error_code), message=metadata.message, data=None)
