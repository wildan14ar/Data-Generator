"""
API v1 router - combines all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1 import generate, seed, files, schemas, system


# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    generate.router,
    prefix="/data",
    tags=["Data Generation"]
)

api_router.include_router(
    seed.router,
    prefix="/database",
    tags=["Database Seeding"]
)

api_router.include_router(
    files.router,
    prefix="/files",
    tags=["File Management"]
)

api_router.include_router(
    schemas.router,
    prefix="/schemas",
    tags=["Schema Validation"]
)

api_router.include_router(
    system.router,
    tags=["System"]
)