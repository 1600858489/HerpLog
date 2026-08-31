from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.infra.database import create_all_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize development database tables during application startup."""
    await create_all_tables()
    yield


from backend.app.core.config import get_settings
from backend.app.core.response import ResponseEnvelope, success_response
from backend.app.middlewares import RequestLoggingMiddleware, register_cors, register_exception_handlers


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

register_exception_handlers(app)
register_cors(app, settings)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/", response_model=ResponseEnvelope[dict[str, str]])
async def read_root() -> ResponseEnvelope[dict[str, str]]:
    """Return the API availability message."""
    return success_response({"message": "HerpLog API is running"})


@app.get("/health", response_model=ResponseEnvelope[dict[str, str]])
async def health_check() -> ResponseEnvelope[dict[str, str]]:
    """Return the API health status."""
    return success_response({"status": "ok"})
