"""
File download endpoints
"""

import logging
from pathlib import Path
import tempfile

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["File Management"])


@router.get("/download/{filename}")
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
        
        # Security check - ensure file is within temp directory
        if not str(file_path.resolve()).startswith(str(temp_dir.resolve())):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
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