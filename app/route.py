"""
Combined routing for data generation and database operations
"""

import time
import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.core.schemas import (
    DataGenerateRequest,
    DataGenerateResponse,
    DatabaseSchemaRequest,
    DatabaseSchemaResponse,
)
from app.services.generator import generate_data
from app.introspector import get_database_schema
from app.services.exporter import get_exporter
from app.core.config import get_settings
from app.core.exceptions import SchemaIntrospectionError, DatabaseError, ExportError


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

    # Update format usage - support all formats
    if "format_usage" not in stats:
        stats["format_usage"] = {}
    stats["format_usage"][format_used] = stats["format_usage"].get(format_used, 0) + 1

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
    """Generate data for multiple related tables with various export formats."""
    start_time = time.time()

    try:
        logger.info(
            f"Generating data for {len(request.schemas)} tables in {request.format.value} format"
        )

        # Generate multi-table data
        table_data = generate_data(request.schemas, request.count)

        generation_time = time.time() - start_time
        total_records = sum(len(data) for data in table_data.values())

        # Update stats
        update_stats(http_request, request.format.value, generation_time, total_records)

        # Handle different export formats
        if request.format.value == "json":
            # Return data directly in response untuk JSON format
            return DataGenerateResponse(
                data=table_data,
                count=request.count,
                tables_generated=len(table_data),
                total_records=total_records,
                format=request.format.value,
                message=f"Successfully generated {total_records} records for {len(table_data)} tables",
            )

        else:
            # Use exporter service untuk formats lain
            exporter = get_exporter()
            export_result = exporter.export_data(
                data=table_data,
                format=request.format.value,
                connection_string=request.connection_string,
                filename_prefix=request.filename_prefix or "datagen",
            )

            # Merge hasil export dengan response data
            response_data = {
                "success": export_result["success"],
                "count": request.count,
                "tables_generated": len(table_data),
                "total_records": total_records,
                "format": request.format.value,
                "message": f"Successfully generated and exported {total_records} records for {len(table_data)} tables",
            }

            # Add format-specific fields
            if request.format.value in ["excel", "sql"]:
                response_data.update(
                    {
                        "export_id": export_result["export_id"],
                        "filename": export_result["filename"],
                        "download_url": export_result["download_url"],
                        "file_size": export_result["file_size"],
                        "expires_at": export_result["expires_at"],
                    }
                )

            elif request.format.value in ["db", "database"]:
                response_data.update(
                    {
                        "export_id": export_result["export_id"],
                        "connection_summary": export_result["connection_summary"],
                        "tables_inserted": export_result["tables_inserted"],
                        "insert_time": export_result["insert_time"],
                    }
                )

            return DataGenerateResponse(**response_data)

    except ExportError as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Multi-table generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================
# File Download Endpoints
# ============================================


@router.get(
    "/files/download/{filename}", tags=["File Management"], response_class=FileResponse
)
async def download_file(filename: str):
    """Download generated file."""
    try:
        exporter = get_exporter()
        file_path = exporter.temp_dir / filename

        if not file_path.exists():
            logger.error(f"File not found: {filename}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{filename}' not found or has expired",
            )

        # Determine media type based on file extension
        media_types = {
            ".json": "application/json",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".sql": "application/sql",
            ".csv": "text/csv",
        }

        file_ext = file_path.suffix.lower()
        media_type = media_types.get(file_ext, "application/octet-stream")

        logger.info(f"Serving file download: {filename}")

        return FileResponse(
            path=str(file_path), filename=filename, media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading file",
        )


@router.delete("/files/cleanup", tags=["File Management"])
async def cleanup_expired_files():
    """Cleanup expired temporary files."""
    try:
        exporter = get_exporter()
        cleaned_count = exporter.cleanup_expired_files(max_age_hours=1)

        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired files",
            "files_cleaned": cleaned_count,
        }

    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during file cleanup",
        )
