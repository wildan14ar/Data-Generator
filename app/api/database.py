"""
Database operations endpoints (introspection and seeding)
"""

import time
import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import (
    SeedRequest,
    SeedResponse,
    DatabaseSchemaRequest,
    DatabaseSchemaResponse,
)
from app.services.generator import generate_data, clear_caches
from app.services.seeder import seed_db, test_connection
from app.services.introspector import get_database_schema
from app.core.exceptions import SchemaIntrospectionError, DatabaseError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/database", tags=["Database Operations"])


def update_stats(request: Request, generation_time: float, records_count: int):
    """Update global statistics for database operations."""
    stats = request.app.state.stats
    stats["total_requests"] += 1
    stats["total_records_generated"] += records_count
    stats["format_usage"]["database"] = stats["format_usage"].get("database", 0) + 1
    stats["generation_times"].append(generation_time)

    # Keep only last 1000 generation times for memory efficiency
    if len(stats["generation_times"]) > 1000:
        stats["generation_times"] = stats["generation_times"][-1000:]


# ============================================
# Database Seeding Endpoints
# ============================================


@router.post("/seed", response_model=SeedResponse)
async def seed_database(request: SeedRequest, http_request: Request):
    """Generate data and seed database."""
    start_time = time.time()

    try:
        logger.info(f"Seeding database table '{request.table_name}'")

        # Test connection first
        if not test_connection(request.connection_string):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot connect to database. Please check connection string.",
            )

        # Clear caches for fresh generation
        clear_caches()

        # Generate data
        data = generate_data(
            request.data_schema, request.count, request.model_name, request.seed
        )

        # Seed database
        seed_db(data, request.connection_string, request.table_name, request.batch_size)

        generation_time = time.time() - start_time
        update_stats(http_request, generation_time, len(data))

        return SeedResponse(
            records_inserted=len(data),
            table_name=request.table_name,
            model_name=request.model_name,
            seed=request.seed,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================
# Database Introspection Endpoints
# ============================================


@router.get("/schema", response_model=DatabaseSchemaResponse)
async def introspect_database_schema(request: DatabaseSchemaRequest):
    """Get JSON Schema for multiple tables or entire database."""
    try:
        tables_info = (
            f"all tables"
            if not request.tables
            else f"tables: {', '.join(request.tables)}"
        )
        logger.info(f"Introspecting database schema for {tables_info}")

        schemas = get_database_schema(request.connection_string, request.tables)

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
