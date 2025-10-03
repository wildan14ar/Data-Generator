"""
SQL export functionality
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from app.config.exceptions import ExportError

logger = logging.getLogger(__name__)


class SqlExporter:
    """SQL export handler."""
    
    def __init__(self, temp_dir: Path):
        """Initialize SQL exporter.
        
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
        """Export data to SQL INSERT statements format.
        
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
            filename = f"{export_id}_{filename_prefix}_{timestamp}.sql"
            file_path = self.temp_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write(f"-- Data Export SQL Script\n")
                f.write(f"-- Export ID: {export_id}\n")
                f.write(f"-- Export Time: {datetime.now().isoformat()}\n")
                f.write(f"-- Tables: {', '.join(data.keys())}\n")
                f.write(f"-- Total Records: {sum(len(records) for records in data.values())}\n\n")
                
                # Generate INSERT statements untuk setiap table
                total_statements = 0
                for table_name, records in data.items():
                    if not records:
                        continue
                    
                    f.write(f"-- Table: {table_name} ({len(records)} records)\n")
                    
                    # Get all columns from first record
                    columns = list(records[0].keys())
                    columns_str = ", ".join(f'"{col}"' for col in columns)
                    
                    # Write INSERT statements in batches
                    batch_size = 1000
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i + batch_size]
                        
                        f.write(f"INSERT INTO \"{table_name}\" ({columns_str}) VALUES\n")
                        
                        values_list = []
                        for record in batch:
                            values = []
                            for col in columns:
                                value = record.get(col)
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str):
                                    # Escape single quotes
                                    escaped = value.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                elif isinstance(value, bool):
                                    values.append("TRUE" if value else "FALSE")
                                elif isinstance(value, (list, dict)):
                                    # Convert complex types to JSON string
                                    json_str = json.dumps(value).replace("'", "''")
                                    values.append(f"'{json_str}'")
                                else:
                                    values.append(str(value))
                            
                            values_list.append(f"    ({', '.join(values)})")
                        
                        f.write(",\n".join(values_list))
                        f.write(";\n\n")
                        total_statements += len(batch)
                
                f.write(f"-- End of export ({total_statements} total INSERT statements)\n")
            
            file_size = file_path.stat().st_size
            
            logger.info(f"Exported SQL file: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "format": "sql",
                "export_id": export_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "tables_exported": len(data),
                "total_records": sum(len(records) for records in data.values()),
                "total_statements": total_statements,
                "download_url": f"/files/download/{filename}",
                "expires_at": self._get_expiration_time()
            }
            
        except Exception as e:
            raise ExportError(f"Failed to export SQL: {e}")
    
    def _get_expiration_time(self) -> str:
        """Get file expiration time (1 hour from now)."""
        from datetime import timedelta
        expiration = datetime.now() + timedelta(hours=1)
        return expiration.isoformat()