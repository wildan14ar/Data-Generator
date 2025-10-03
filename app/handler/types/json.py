"""
JSON export functionality
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from app.core.exceptions import ExportError

logger = logging.getLogger(__name__)


class JsonExporter:
    """JSON export handler."""
    
    def __init__(self, temp_dir: Path):
        """Initialize JSON exporter.
        
        Args:
            temp_dir: Temporary directory for file storage
        """
        self.temp_dir = temp_dir
    
    def export(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        export_id: str,
        filename_prefix: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """Export data to JSON format.
        
        Args:
            data: Dictionary with table_name -> list of records
            export_id: Unique export identifier
            filename_prefix: Prefix for filename
            timestamp: Timestamp string
            
        Returns:
            Export result dictionary
            
        Raises:
            ExportError: If export fails
        """
        try:
            filename = f"{export_id}_{filename_prefix}_{timestamp}.json"
            file_path = self.temp_dir / filename
            
            # Prepare data dengan metadata
            export_data = {
                "metadata": {
                    "export_id": export_id,
                    "export_time": datetime.now().isoformat(),
                    "format": "json",
                    "tables": list(data.keys()),
                    "total_records": sum(len(records) for records in data.values())
                },
                "data": data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            file_size = file_path.stat().st_size
            
            logger.info(f"Exported JSON file: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "format": "json",
                "export_id": export_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "tables_exported": len(data),
                "total_records": sum(len(records) for records in data.values()),
                "download_url": f"/files/download/{filename}",
                "expires_at": self._get_expiration_time()
            }
            
        except Exception as e:
            raise ExportError(f"Failed to export JSON: {e}")
    
    def _get_expiration_time(self) -> str:
        """Get file expiration time (1 hour from now)."""
        from datetime import timedelta
        expiration = datetime.now() + timedelta(hours=1)
        return expiration.isoformat()