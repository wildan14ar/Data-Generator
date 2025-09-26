"""
Data generation endpoints
"""

import time
import uuid
import tempfile
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, status
from fastapi.responses import FileResponse

from app.models.schemas import (
    GenerateRequest, GenerateResponse, GenerateFileRequest,
    ExportFormat
)
from app.services.generator import generate_data, clear_caches
from app.services.exporter import export_json, export_csv, export_sql, export_parquet
from app.core.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["Data Generation"])
settings = get_settings()


def update_stats(request: Request, format_used: str, generation_time: float, records_count: int):
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


@router.post("/generate", response_model=GenerateResponse)
async def generate_data_endpoint(
    request: GenerateRequest,
    http_request: Request
):
    """Generate data and return in response."""
    start_time = time.time()
    
    try:
        # Clear caches for fresh generation
        clear_caches()
        
        logger.info(f"Generating {request.count} records")
        
        # Generate data
        data = generate_data(
            request.data_schema,
            request.count,
            request.model_name,
            request.seed
        )
        
        generation_time = time.time() - start_time
        update_stats(http_request, request.format.value, generation_time, len(data))
        
        return GenerateResponse(
            data=data,
            count=len(data),
            model_name=request.model_name,
            seed=request.seed,
            format=request.format.value
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/generate/file")
async def generate_to_file(
    request: GenerateFileRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
):
    """Generate data and save to file, return download link."""
    start_time = time.time()
    
    try:
        # Clear caches for fresh generation
        clear_caches()
        
        logger.info(f"Generating {request.count} records to file")
        
        # Generate data
        data = generate_data(
            request.data_schema,
            request.count,
            request.model_name,
            request.seed
        )
        
        # Create temp file
        temp_dir = Path(tempfile.gettempdir()) / "datagen_api"
        temp_dir.mkdir(exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_extension = f".{request.format.value}"
        temp_file = temp_dir / f"{file_id}_{request.filename}{file_extension}"
        
        # Export data
        if request.format == ExportFormat.json:
            export_json(data, str(temp_file))
        elif request.format == ExportFormat.csv:
            export_csv(data, str(temp_file))
        elif request.format == ExportFormat.sql:
            export_sql(data, request.table_name, str(temp_file))
        elif request.format == ExportFormat.parquet:
            export_parquet(data, str(temp_file))
        
        generation_time = time.time() - start_time
        update_stats(http_request, request.format.value, generation_time, len(data))
        
        # Schedule file cleanup after configured time
        cleanup_hours = settings.FILE_CLEANUP_HOURS
        background_tasks.add_task(cleanup_file, temp_file, cleanup_hours * 3600)
        
        return {
            "success": True,
            "message": "File generated successfully",
            "file_id": file_id,
            "filename": f"{file_id}_{request.filename}{file_extension}",
            "download_url": f"/files/download/{file_id}_{request.filename}{file_extension}",
            "count": len(data),
            "format": request.format.value,
            "expires_in": f"{cleanup_hours} hour{'s' if cleanup_hours != 1 else ''}"
        }
        
    except Exception as e:
        logger.error(f"File generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )