from fastapi import APIRouter

from .classification import classification_router
from .lifecycle import lifecycle_router
from .management import management_router
from .pet import pet_router as pet_resource_router

pet_router = APIRouter()
pet_router.include_router(classification_router)
pet_router.include_router(management_router)
pet_router.include_router(lifecycle_router)
pet_router.include_router(pet_resource_router)

__all__ = ["pet_router"]
