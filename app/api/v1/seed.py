"""
Database seeding endpoints
"""

import time
import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import SeedRequest, SeedResponse
from app.services.generator import generate_data, clear_caches
from app.services.seeder import seed_db, test_connection


logger = logging.getLogger(__name__)
router = APIRouter()


def update_stats(request: Request, generation_time: float, records_count: int):
    """Update global statistics for database seeding."""
    stats = request.app.state.stats
    stats["total_requests"] += 1
    stats["total_records_generated"] += records_count
    stats["format_usage"]["database"] = stats["format_usage"].get("database", 0) + 1
    stats["generation_times"].append(generation_time)
    
    # Keep only last 1000 generation times for memory efficiency
    if len(stats["generation_times"]) > 1000:
        stats["generation_times"] = stats["generation_times"][-1000:]


@router.post("/seed", response_model=SeedResponse)
async def seed_database(
    request: SeedRequest,
    http_request: Request
):
    """Generate data and seed database."""
    start_time = time.time()
    
    try:
        logger.info(f"Seeding database table '{request.table_name}'")
        
        # Test connection first
        if not test_connection(request.connection_string):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot connect to database. Please check connection string."
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
        update_stats(http_request, generation_time, len(data))
        
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
            detail=str(e)
        )