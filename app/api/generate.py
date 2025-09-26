"""
Data generation and file management endpoints
"""

import time
import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    GenerateMultiTableRequest,
    GenerateMultiTableResponse,
)
from app.services.generator import (
    generate_data,
    generate_multi_table_data,
    clear_caches,
)
from app.core.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["Data Generation & Files"])
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
# Data Generation Endpoints
# ============================================


@router.post("/generate", response_model=GenerateResponse)
async def generate_data_endpoint(request: GenerateRequest, http_request: Request):
    """Generate data and return in response."""
    start_time = time.time()

    try:
        # Clear caches for fresh generation
        clear_caches()

        logger.info(f"Generating {request.count} records")

        # Generate data
        data = generate_data(
            request.data_schema, request.count, request.model_name, request.seed
        )

        generation_time = time.time() - start_time
        update_stats(http_request, request.format.value, generation_time, len(data))

        return GenerateResponse(
            data=data,
            count=len(data),
            model_name=request.model_name,
            seed=request.seed,
            format=request.format.value,
        )

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/generate/multi-table", response_model=GenerateMultiTableResponse)
async def generate_multi_table_endpoint(
    request: GenerateMultiTableRequest, http_request: Request
):
    """Generate data for multiple related tables."""
    start_time = time.time()

    try:
        logger.info(f"Generating data for {len(request.schemas)} tables")

        # Generate multi-table data
        table_data = generate_multi_table_data(
            request.schemas, request.count, request.seed
        )

        generation_time = time.time() - start_time
        total_records = sum(len(data) for data in table_data.values())

        # Update stats
        update_stats(http_request, request.format.value, generation_time, total_records)

        return GenerateMultiTableResponse(
            data=table_data,
            count=request.count,
            tables_generated=len(table_data),
            total_records=total_records,
            seed=request.seed,
            format=request.format.value,
        )

    except Exception as e:
        logger.error(f"Multi-table generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
