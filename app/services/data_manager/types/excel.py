"""
Excel export functionality
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from app.config.exceptions import ExportError

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Excel export handler."""
    
    def __init__(self, temp_dir: Path):
        """Initialize Excel exporter.
        
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
        """Export data to Excel format with multiple sheets.
        
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
            filename = f"{export_id}_{filename_prefix}_{timestamp}.xlsx"
            file_path = self.temp_dir / filename
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Create metadata sheet
                metadata_df = pd.DataFrame([
                    ["Export ID", export_id],
                    ["Export Time", datetime.now().isoformat()],
                    ["Format", "excel"],
                    ["Tables", ", ".join(data.keys())],
                    ["Total Records", sum(len(records) for records in data.values())]
                ], columns=["Property", "Value"])
                
                metadata_df.to_excel(writer, sheet_name="Metadata", index=False)
                
                # Create sheet untuk setiap table
                for table_name, records in data.items():
                    if records:  # Only create sheet if there are records
                        df = pd.DataFrame(records)
                        
                        # Limit sheet name length (Excel limitation)
                        sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        logger.info(f"Created Excel sheet '{sheet_name}' with {len(records)} records")
            
            file_size = file_path.stat().st_size
            
            logger.info(f"Exported Excel file: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "format": "excel",
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
            raise ExportError(f"Failed to export Excel: {e}")
    
    def _get_expiration_time(self) -> str:
        """Get file expiration time (1 hour from now)."""
        from datetime import timedelta
        expiration = datetime.now() + timedelta(hours=1)
        return expiration.isoformat()