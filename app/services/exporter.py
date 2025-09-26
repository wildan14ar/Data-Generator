"""
Data export service untuk berbagai format
"""

import json
import logging
import pandas as pd
import sqlalchemy as sa
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import tempfile
import uuid

from app.core.exceptions import ExportError
from app.services.seeder import seed_db


logger = logging.getLogger(__name__)


class DataExporter:
    """Service untuk export data ke berbagai format."""
    
    def __init__(self, temp_dir: str = "temp"):
        """Initialize exporter dengan temp directory."""
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def export_data(
        self,
        data: Dict[str, List[Dict[str, Any]]], 
        format: str,
        connection_string: Optional[str] = None,
        filename_prefix: str = "datagen"
    ) -> Dict[str, Any]:
        """
        Export data ke format yang diminta.
        
        Args:
            data: Dictionary dengan table_name -> list of records
            format: Format export (json, excel, sql, db)
            connection_string: Connection string untuk database (jika format=db)
            filename_prefix: Prefix untuk nama file
            
        Returns:
            Dictionary dengan informasi export result
        """
        if not data:
            raise ExportError("No data to export")
        
        export_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if format.lower() == "json":
                return self._export_json(data, export_id, filename_prefix, timestamp)
            
            elif format.lower() == "excel":
                return self._export_excel(data, export_id, filename_prefix, timestamp)
            
            elif format.lower() == "sql":
                return self._export_sql(data, export_id, filename_prefix, timestamp)
            
            elif format.lower() in ["db", "database"]:
                return self._export_database(data, connection_string, export_id)
            
            else:
                raise ExportError(f"Unsupported export format: {format}")
                
        except ExportError:
            raise
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise ExportError(f"Failed to export data: {e}")
    
    def _export_json(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        export_id: str,
        filename_prefix: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """Export data ke format JSON."""
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
    
    def _export_excel(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        export_id: str,
        filename_prefix: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """Export data ke format Excel dengan multiple sheets."""
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
    
    def _export_sql(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        export_id: str,
        filename_prefix: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """Export data ke format SQL INSERT statements."""
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
    
    def _export_database(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        connection_string: str,
        export_id: str
    ) -> Dict[str, Any]:
        """Export data langsung ke database."""
        if not connection_string:
            raise ExportError("Connection string is required for database export")
        
        try:
            total_inserted = 0
            tables_inserted = []
            
            for table_name, records in data.items():
                if records:
                    logger.info(f"Seeding table '{table_name}' with {len(records)} records")
                    seed_db(records, connection_string, table_name)
                    total_inserted += len(records)
                    tables_inserted.append(table_name)
            
            logger.info(f"Successfully seeded {total_inserted} records to {len(tables_inserted)} tables")
            
            return {
                "success": True,
                "format": "database",
                "export_id": export_id,
                "connection_summary": self._mask_connection_string(connection_string),
                "tables_inserted": tables_inserted,
                "total_records": total_inserted,
                "insert_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ExportError(f"Failed to export to database: {e}")
    
    def _get_expiration_time(self) -> str:
        """Get file expiration time (1 hour from now)."""
        from datetime import timedelta
        expiration = datetime.now() + timedelta(hours=1)
        return expiration.isoformat()
    
    def _mask_connection_string(self, conn_str: str) -> str:
        """Mask sensitive information in connection string."""
        try:
            # Simple masking - hide password
            import re
            masked = re.sub(r'://[^:]+:[^@]+@', '://***:***@', conn_str)
            return masked
        except:
            return "***masked***"
    
    def cleanup_expired_files(self, max_age_hours: int = 1) -> int:
        """
        Cleanup expired files dari temp directory.
        
        Args:
            max_age_hours: Maximum age of files in hours
            
        Returns:
            Number of files cleaned up
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            cleaned_count = 0
            for file_path in self.temp_dir.glob("*"):
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


# Global exporter instance
_exporter = None


def get_exporter() -> DataExporter:
    """Get global exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = DataExporter()
    return _exporter