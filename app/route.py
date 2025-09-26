"""
Combined routing for data generation and database operations
"""

import time
import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import (
    DataGenerateRequest,
    DataGenerateResponse,
    DatabaseSchemaRequest,
    DatabaseSchemaResponse,
)
from app.services.generator import generate_data
from app.services.introspector import get_database_schema
from app.core.config import get_settings
from app.core.exceptions import SchemaIntrospectionError, DatabaseError


logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def update_stats(
    request: Request, format_used: str, generation_time: float, records_count: int
):
    """Update global statistics."""
    stats = request.app.state.stats
    stats["total_requests"] += 1
    stats["total_records_generated"] += records_count
    stats["format_usage"][format_used] += 1
    stats["generation_times"].append(generation_time)

    # Keep only last 1000 generation times for memory efficiency
    if len(stats["generation_times"]) > 1000:
        stats["generation_times"] = stats["generation_times"][-1000:]


def update_database_stats(request: Request, generation_time: float, records_count: int):
    """Update global statistics for database operations."""
    stats = request.app.state.stats
    stats["total_requests"] += 1
    stats["total_records_generated"] += records_count
    stats["format_usage"]["database"] = stats["format_usage"].get("database", 0) + 1
    stats["generation_times"].append(generation_time)

    # Keep only last 1000 generation times for memory efficiency
    if len(stats["generation_times"]) > 1000:
        stats["generation_times"] = stats["generation_times"][-1000:]


async def cleanup_file(file_path: Path, delay: int):
    """Cleanup temporary file after delay."""
    await asyncio.sleep(delay)
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup file {file_path}: {e}")


# ============================================
# Database Operations Endpoints
# ============================================


@router.get(
    "/database/schema",
    response_model=DatabaseSchemaResponse,
    tags=["Database Operations"],
)
async def introspect_database_schema(request: DatabaseSchemaRequest):
    """Get JSON Schema for entire database."""
    try:
        logger.info("Introspecting database schema for all tables")

        schemas = get_database_schema(request.connection_string)

        return DatabaseSchemaResponse(
            schemas=schemas,
            table_count=len(schemas),
            message=f"Database schema retrieved successfully for {len(schemas)} tables",
        )

    except DatabaseError as e:
        logger.error(f"Database error during database schema introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database connection failed: {str(e)}",
        )
    except SchemaIntrospectionError as e:
        logger.error(f"Schema introspection error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during database schema introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during database schema introspection",
        )


# ============================================
# Data Generation Endpoints
# ============================================


@router.post(
    "/data/generate", response_model=DataGenerateResponse, tags=["Data Generation"]
)
async def generate_endpoint(request: DataGenerateRequest, http_request: Request):
    """Generate data for multiple related tables."""
    start_time = time.time()

    try:
        logger.info(f"Generating data for {len(request.schemas)} tables")

        # Generate multi-table data
        table_data = generate_data(request.schemas, request.count)

        generation_time = time.time() - start_time
        total_records = sum(len(data) for data in table_data.values())

        # Update stats
        update_stats(http_request, request.format.value, generation_time, total_records)

        return DataGenerateResponse(
            data=table_data,
            count=request.count,
            tables_generated=len(table_data),
            total_records=total_records,
            format=request.format.value,
        )

    except Exception as e:
        logger.error(f"Multi-table generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
