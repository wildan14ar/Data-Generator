"""
Main API router - combines all endpoint routers without versioning
"""

from fastapi import APIRouter

from app.api.endpoints import generate, seed, files, schemas, system, introspect


# Create main API router
api_router = APIRouter()

# Include all endpoint routers (prefixes and tags are defined in each router)
api_router.include_router(generate.router)
api_router.include_router(seed.router)
api_router.include_router(files.router)
api_router.include_router(schemas.router)
api_router.include_router(system.router)
api_router.include_router(introspect.router)