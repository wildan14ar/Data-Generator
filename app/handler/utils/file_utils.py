"""
File management utilities
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def cleanup_expired_files(temp_dir: Path, max_age_hours: int = 1) -> int:
    """Cleanup expired files dari temp directory.
    
    Args:
        temp_dir: Directory to clean
        max_age_hours: Maximum age of files in hours
        
    Returns:
        Number of files cleaned up
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        cleaned_count = 0
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up expired file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup file {file_path}: {e}")
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")
        return 0


def get_file_info(file_path: Path) -> dict:
    """Get file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True
        }
    except Exception as e:
        return {
            "name": str(file_path),
            "error": str(e),
            "exists": False
        }