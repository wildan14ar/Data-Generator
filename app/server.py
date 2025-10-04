"""
FastAPI application factory and configuration
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.route import router
from app.core.schemas import (
    HealthResponse,
    StatsResponse,
)
from app.core.Settings import get_settings
from app.core.exceptions import setup_exception_handlers


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("🚀 Starting Datagen API...")
    app.state.start_time = datetime.now()
    app.state.stats = {
        "total_requests": 0,
        "total_records_generated": 0,
        "format_usage": {"json": 0, "excel": 0, "sql": 0, "database": 0},
        "generation_times": [],
    }

    yield

    # Shutdown
    logger.info("🛑 Shutting down Datagen API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Add middleware
    if settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Health check endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic API information."""
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
            "docs_url": "/docs" if settings.DEBUG else None,
            "health_check": "/health",
        }

    # System endpoints (health, stats) - directly in main app
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check(request: Request):
        """Health check endpoint."""
        start_time = getattr(request.app.state, "start_time", datetime.now())
        uptime = datetime.now() - start_time
        return HealthResponse(
            timestamp=datetime.now().isoformat(),
            version=settings.VERSION,
            uptime=str(uptime),
        )

    @app.get("/stats", response_model=StatsResponse, tags=["System"])
    async def get_stats(request: Request):
        """Get API usage statistics."""
        start_time = getattr(request.app.state, "start_time", datetime.now())
        stats = getattr(
            request.app.state,
            "stats",
            {
                "total_requests": 0,
                "total_records_generated": 0,
                "format_usage": {},
                "generation_times": [],
            },
        )

        uptime = datetime.now() - start_time
        avg_time = (
            (sum(stats["generation_times"]) / len(stats["generation_times"]))
            if stats["generation_times"]
            else 0
        )

        return StatsResponse(
            total_requests=stats["total_requests"],
            total_records_generated=stats["total_records_generated"],
            popular_formats=stats["format_usage"],
            average_generation_time=avg_time,
            uptime_hours=uptime.total_seconds() / 3600,
        )

    # Include API routers with prefix
    app.include_router(router)

    return app


# Create the application instance
app = create_app()
