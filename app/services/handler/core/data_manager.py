"""
Main data manager core functionality
"""

import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.config.exceptions import ExportError, DatabaseError
from ..types.json import JsonExporter
from ..types.excel import ExcelExporter
from ..types.sql import SqlExporter
from ..types.seeder import DatabaseSeeder
from ..utils.connection_utils import test_connection, mask_connection_string
from ..utils.file_utils import cleanup_expired_files

logger = logging.getLogger(__name__)


class DataManager:
    """Unified service untuk export dan seeding data."""
    
    def __init__(self, temp_dir: str = "temp"):
        """Initialize data manager.
        
        Args:
            temp_dir: Temporary directory for file storage
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize exporters
        self.json_exporter = JsonExporter(self.temp_dir)
        self.excel_exporter = ExcelExporter(self.temp_dir)
        self.sql_exporter = SqlExporter(self.temp_dir)
        
        # Initialize seeder
        self.database_seeder = DatabaseSeeder()
    
    def export_data(
        self,
        data: Dict[str, List[Dict[str, Any]]], 
        format: str,
        connection_string: Optional[str] = None,
        filename_prefix: str = "datagen"
    ) -> Dict[str, Any]:
        """Export data ke format yang diminta.
        
        Args:
            data: Dictionary dengan table_name -> list of records
            format: Format export (json, excel, sql, db)
            connection_string: Connection string untuk database (jika format=db)
            filename_prefix: Prefix untuk nama file
            
        Returns:
            Dictionary dengan informasi export result
            
        Raises:
            ExportError: If export fails
            DatabaseError: If database export fails
        """
        if not data:
            raise ExportError("No data to export")
        
        export_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            format_lower = format.lower()
            
            if format_lower == "json":
                return self.json_exporter.export(data, export_id, filename_prefix, timestamp)
            
            elif format_lower == "excel":
                return self.excel_exporter.export(data, export_id, filename_prefix, timestamp)
            
            elif format_lower == "sql":
                return self.sql_exporter.export(data, export_id, filename_prefix, timestamp)
            
            elif format_lower in ["db", "database"]:
                return self._export_database(data, connection_string, export_id)
            
            else:
                raise ExportError(f"Unsupported export format: {format}")
                
        except (ExportError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Export error: {e}")
            raise ExportError(f"Failed to export data: {e}")
    
    def _export_database(
        self, 
        data: Dict[str, List[Dict[str, Any]]], 
        connection_string: str,
        export_id: str
    ) -> Dict[str, Any]:
        """Export data langsung ke database.
        
        Args:
            data: Dictionary dengan table_name -> list of records
            connection_string: Database connection string
            export_id: Unique export identifier
            
        Returns:
            Export result dictionary
            
        Raises:
            DatabaseError: If database export fails
        """
        if not connection_string:
            raise DatabaseError("Connection string is required for database export")
        
        # Test connection first
        if not test_connection(connection_string):
            raise DatabaseError("Failed to connect to database")
        
        try:
            total_inserted = 0
            tables_inserted = []
            seeding_results = {}
            
            for table_name, records in data.items():
                if records:
                    logger.info(f"Seeding table '{table_name}' with {len(records)} records")
                    result = self.database_seeder.seed(records, connection_string, table_name)
                    
                    if result["success"]:
                        total_inserted += result["records_inserted"]
                        tables_inserted.append(table_name)
                        seeding_results[table_name] = result
                    else:
                        logger.error(f"Failed to seed table '{table_name}': {result.get('error', 'Unknown error')}")
                        raise DatabaseError(f"Failed to seed table '{table_name}': {result.get('error', 'Unknown error')}")
            
            logger.info(f"Successfully seeded {total_inserted} records to {len(tables_inserted)} tables")
            
            return {
                "success": True,
                "format": "database",
                "export_id": export_id,
                "connection_summary": mask_connection_string(connection_string),
                "tables_inserted": tables_inserted,
                "total_records": total_inserted,
                "seeding_results": seeding_results,
                "insert_time": datetime.now().isoformat()
            }
            
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Database export error: {e}")
            raise DatabaseError(f"Failed to export to database: {e}")
    
    def seed_database(
        self,
        data: List[Dict[str, Any]],
        connection_string: str,
        table_name: str,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """Seed database dengan data untuk single table.
        
        Args:
            data: List of records to insert
            connection_string: Database connection string
            table_name: Target table name
            batch_size: Number of records per batch
            
        Returns:
            Seeding result dictionary
            
        Raises:
            DatabaseError: If seeding fails
        """
        if not test_connection(connection_string):
            raise DatabaseError("Failed to connect to database")
        
        return self.database_seeder.seed(data, connection_string, table_name, batch_size)
    
    def cleanup_expired_files(self, max_age_hours: int = 1) -> int:
        """Cleanup expired files dari temp directory.
        
        Args:
            max_age_hours: Maximum age of files in hours
            
        Returns:
            Number of files cleaned up
        """
        return cleanup_expired_files(self.temp_dir, max_age_hours)
    
    def get_export_formats(self) -> List[str]:
        """Get list of supported export formats.
        
        Returns:
            List of supported formats
        """
        return ["json", "excel", "sql", "database"]
    
    def get_temp_dir_info(self) -> Dict[str, Any]:
        """Get information about temporary directory.
        
        Returns:
            Dictionary with temp dir information
        """
        try:
            files = list(self.temp_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            return {
                "path": str(self.temp_dir),
                "file_count": len([f for f in files if f.is_file()]),
                "total_size": total_size,
                "files": [f.name for f in files if f.is_file()]
            }
        except Exception as e:
            logger.error(f"Error getting temp dir info: {e}")
            return {
                "path": str(self.temp_dir),
                "error": str(e)
            }


# Global data manager instance
_data_manager = None


def get_data_manager() -> DataManager:
    """Get global data manager instance.
    
    Returns:
        DataManager instance
    """
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager