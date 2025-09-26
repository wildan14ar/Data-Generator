"""
System endpoints (health, stats)
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Request

from app.models.schemas import HealthResponse, StatsResponse
from app.core.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
        version=settings.VERSION,
        uptime=str(datetime.now() - datetime.now())  # Will be overridden by app state
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(request: Request):
    """Get API usage statistics."""
    start_time = getattr(request.app.state, 'start_time', datetime.now())
    stats = getattr(request.app.state, 'stats', {
        "total_requests": 0,
        "total_records_generated": 0,
        "format_usage": {},
        "generation_times": []
    })
    
    uptime = datetime.now() - start_time
    avg_time = (sum(stats["generation_times"]) / len(stats["generation_times"])) if stats["generation_times"] else 0
    
    return StatsResponse(
        total_requests=stats["total_requests"],
        total_records_generated=stats["total_records_generated"],
        popular_formats=stats["format_usage"],
        average_generation_time=avg_time,
        uptime_hours=uptime.total_seconds() / 3600
    )