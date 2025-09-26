"""
FastAPI application factory and configuration
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import setup_exception_handlers


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        "format_usage": {"json": 0, "csv": 0, "sql": 0, "parquet": 0},
        "generation_times": []
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
        lifespan=lifespan
    )
    
    # Add middleware
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Health check endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic API information."""
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "running",
            "docs_url": "/docs" if settings.DEBUG else None,
            "health_check": "/api/v1/health"
        }
    
    return app


# Create the application instance
app = create_app()