import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..core.errors import BusinessError, ErrorCode, get_error_metadata
from ..core.response import error_response

logger = logging.getLogger(__name__)


async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    """Convert an expected business failure into its public API envelope."""
    metadata = get_error_metadata(exc.error_code)
    return JSONResponse(status_code=metadata.http_status, content=error_response(exc.error_code).model_dump())


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a safe natural-language response for invalid request data."""
    return JSONResponse(
        status_code=422,
        content=error_response(ErrorCode.INVALID_REQUEST).model_dump(),
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Map framework HTTP errors to the common response shape."""
    code = ErrorCode.UNAUTHORIZED if exc.status_code == 401 else ErrorCode.INVALID_REQUEST
    return JSONResponse(status_code=exc.status_code, content=error_response(code).model_dump())


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures server-side while hiding implementation details."""
    logger.exception("Unhandled request error: %s %s", request.method, request.url.path)
    metadata = get_error_metadata(ErrorCode.SYSTEM_ERROR)
    return JSONResponse(status_code=metadata.http_status, content=error_response(ErrorCode.SYSTEM_ERROR).model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register all safe API exception mappings on the FastAPI application."""
    app.add_exception_handler(BusinessError, business_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
