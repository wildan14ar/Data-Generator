"""
FastAPI main application for Datagen API
"""

import os
import sys
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import generate_data, clear_caches
from exporters import export_json, export_csv, export_sql, export_parquet
from seeder import seed_db, test_connection
from cli import load_schema

from .models import (
    GenerateRequest, GenerateResponse, GenerateFileRequest,
    SeedRequest, SeedResponse, ErrorResponse,
    SchemaValidationRequest, SchemaValidationResponse,
    HealthResponse, GenerateStatsResponse, ExportFormat
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App initialization
app = FastAPI(
    title="Datagen API",
    description="Schema-Aware Data Generator RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global statistics
app_stats = {
    "start_time": datetime.now(),
    "total_requests": 0,
    "total_records_generated": 0,
    "format_usage": {"json": 0, "csv": 0, "sql": 0, "parquet": 0},
    "generation_times": []
}

# Security (optional)
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication. Remove or implement based on needs."""
    # For now, allow all requests
    return {"username": "anonymous"}

def update_stats(format_used: str, generation_time: float, records_count: int):
    """Update global statistics."""
    app_stats["total_requests"] += 1
    app_stats["total_records_generated"] += records_count
    app_stats["format_usage"][format_used] += 1
    app_stats["generation_times"].append(generation_time)
    
    # Keep only last 1000 generation times for memory efficiency
    if len(app_stats["generation_times"]) > 1000:
        app_stats["generation_times"] = app_stats["generation_times"][-1000:]

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc),
            error_type="InternalError"
        ).dict()
    )

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "service": "Datagen API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    uptime = datetime.now() - app_stats["start_time"]
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
        uptime=str(uptime)
    )

@app.get("/stats", response_model=GenerateStatsResponse)
async def get_stats():
    """Get API usage statistics."""
    uptime = datetime.now() - app_stats["start_time"]
    avg_time = (sum(app_stats["generation_times"]) / len(app_stats["generation_times"])) if app_stats["generation_times"] else 0
    
    return GenerateStatsResponse(
        total_requests=app_stats["total_requests"],
        total_records_generated=app_stats["total_records_generated"],
        popular_formats=app_stats["format_usage"],
        average_generation_time=avg_time,
        uptime_hours=uptime.total_seconds() / 3600
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate_data_endpoint(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate data and return in response."""
    start_time = time.time()
    
    try:
        # Clear caches for fresh generation
        clear_caches()
        
        logger.info(f"Generating {request.count} records for user {current_user.get('username')}")
        
        # Generate data
        data = generate_data(
            request.schema,
            request.count,
            request.model_name,
            request.seed
        )
        
        generation_time = time.time() - start_time
        update_stats(request.format.value, generation_time, len(data))
        
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
            detail=ErrorResponse(
                error=str(e),
                error_type="GenerationError"
            ).dict()
        )

@app.post("/generate/file")
async def generate_to_file(
    request: GenerateFileRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Generate data and save to file, return download link."""
    start_time = time.time()
    
    try:
        # Clear caches for fresh generation
        clear_caches()
        
        logger.info(f"Generating {request.count} records to file for user {current_user.get('username')}")
        
        # Generate data
        data = generate_data(
            request.schema,
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
        update_stats(request.format.value, generation_time, len(data))
        
        # Schedule file cleanup after 1 hour
        background_tasks.add_task(cleanup_file, temp_file, 3600)
        
        return {
            "success": True,
            "message": "File generated successfully",
            "file_id": file_id,
            "filename": f"{file_id}_{request.filename}{file_extension}",
            "download_url": f"/download/{file_id}_{request.filename}{file_extension}",
            "count": len(data),
            "format": request.format.value,
            "expires_in": "1 hour"
        }
        
    except Exception as e:
        logger.error(f"File generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=str(e),
                error_type="FileGenerationError"
            ).dict()
        )

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated file."""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "datagen_api"
        file_path = temp_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or expired"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File download failed"
        )

@app.post("/seed", response_model=SeedResponse)
async def seed_database(
    request: SeedRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate data and seed database."""
    start_time = time.time()
    
    try:
        logger.info(f"Seeding database for user {current_user.get('username')}")
        
        # Test connection first
        if not test_connection(request.connection_string):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot connect to database"
            )
        
        # Clear caches for fresh generation
        clear_caches()
        
        # Generate data
        data = generate_data(
            request.schema,
            request.count,
            request.model_name,
            request.seed
        )
        
        # Seed database
        seed_db(
            data,
            request.connection_string,
            request.table_name,
            request.batch_size
        )
        
        generation_time = time.time() - start_time
        update_stats("database", generation_time, len(data))
        
        return SeedResponse(
            records_inserted=len(data),
            table_name=request.table_name,
            model_name=request.model_name,
            seed=request.seed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=str(e),
                error_type="SeedingError"
            ).dict()
        )

@app.post("/validate-schema", response_model=SchemaValidationResponse)
async def validate_schema(request: SchemaValidationRequest):
    """Validate JSON schema."""
    try:
        schema = request.schema
        errors = []
        warnings = []
        
        # Basic validation
        if 'type' not in schema:
            errors.append("Schema must have a 'type' property")
        
        if schema.get('type') == 'object' and 'properties' not in schema:
            warnings.append("Object schema without properties may generate empty objects")
        
        # Check for supported features
        supported_features = []
        if 'enum' in schema or any('enum' in prop for prop in schema.get('properties', {}).values() if isinstance(prop, dict)):
            supported_features.append("enums")
        if 'format' in schema or any('format' in prop for prop in schema.get('properties', {}).values() if isinstance(prop, dict)):
            supported_features.append("string_formats")
        if any(prop.get('type') == 'ref' for prop in schema.get('properties', {}).values() if isinstance(prop, dict)):
            supported_features.append("references")
        
        return SchemaValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_type=schema.get('type'),
            supported_features=supported_features
        )
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schema validation error: {str(e)}"
        )

async def cleanup_file(file_path: Path, delay: int):
    """Cleanup temporary file after delay."""
    await asyncio.sleep(delay)
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup file {file_path}: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )