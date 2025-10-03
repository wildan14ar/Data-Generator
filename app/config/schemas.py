"""
Pydantic models for API requests and responses
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""

    json = "json"
    excel = "excel"
    sql = "sql"
    db = "database"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field("healthy", description="Service health status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field("1.0.0", description="API version")
    uptime: str = Field(..., description="Service uptime")


class StatsResponse(BaseModel):
    """Statistics response for generation operations."""

    total_requests: int = Field(0, description="Total generation requests")
    total_records_generated: int = Field(0, description="Total records generated")
    popular_formats: Dict[str, int] = Field(
        default_factory=dict, description="Usage by format"
    )
    average_generation_time: float = Field(
        0.0, description="Average generation time in seconds"
    )
    uptime_hours: float = Field(0.0, description="Service uptime in hours")


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    error_type: str = Field("GeneralError", description="Type of error")
    status_code: int = Field(400, description="HTTP status code")

class DatabaseSchemaRequest(BaseModel):
    """Request model for getting database schema (all tables)."""

    connection_string: str = Field(..., description="Database connection string")

    @validator("connection_string")
    def validate_connection_string(cls, v):
        """Validate connection string format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Connection string cannot be empty")

        supported_drivers = ["postgresql", "mysql", "sqlite", "mssql"]
        if not any(driver in v.lower() for driver in supported_drivers):
            raise ValueError(
                f"Unsupported database driver. Supported: {supported_drivers}"
            )

        return v


class DatabaseSchemaResponse(BaseModel):
    """Response model for database schema."""

    success: bool = Field(True, description="Whether the operation succeeded")
    schemas: Dict[str, Dict[str, Any]] = Field(..., description="Schema for each table")
    table_count: int = Field(..., description="Number of tables processed")
    message: str = Field(
        "Database schema retrieved successfully", description="Status message"
    )



class DataGenerateRequest(BaseModel):
    """Request model for generating multiple tables with relations."""

    schemas: Dict[str, Dict[str, Any]] = Field(
        ..., description="Multiple table schemas (table_name -> schema)"
    )
    count: Dict[str, int] = Field(
        ..., description="Number of records per table (table_name -> count)"
    )
    format: ExportFormat = Field(ExportFormat.json, description="Export format")
    connection_string: Optional[str] = Field(
        None, description="Database connection string (required for database format)"
    )
    filename_prefix: Optional[str] = Field(
        "datagen", description="Prefix for exported filenames"
    )

    @validator("schemas")
    def validate_schemas(cls, v):
        """Validate that all schemas are valid."""
        if not isinstance(v, dict):
            raise ValueError("Schemas must be a dictionary")

        for table_name, schema in v.items():
            if not isinstance(schema, dict):
                raise ValueError(
                    f"Schema for table '{table_name}' must be a dictionary"
                )
            if "type" not in schema:
                raise ValueError(
                    f"Schema for table '{table_name}' must have a 'type' property"
                )

        return v

    @validator("count")
    def validate_count(cls, v, values):
        """Validate count matches schema tables."""
        schemas = values.get("schemas", {})
        if not isinstance(v, dict):
            raise ValueError("Count must be a dictionary")

        # Check all schemas have counts
        missing_counts = set(schemas.keys()) - set(v.keys())
        if missing_counts:
            raise ValueError(f"Missing count for tables: {missing_counts}")

        # Validate count values
        for table_name, count in v.items():
            if not isinstance(count, int) or count <= 0:
                raise ValueError(
                    f"Count for table '{table_name}' must be a positive integer"
                )
            if count > 100000:
                raise ValueError(
                    f"Count for table '{table_name}' exceeds maximum limit (100000)"
                )

        return v

    @validator("connection_string")
    def validate_connection_string_if_needed(cls, v, values):
        """Validate connection string if format is database."""
        format_val = values.get("format")
        if format_val and format_val.value in ["db", "database"]:
            if not v or len(v.strip()) == 0:
                raise ValueError("Connection string is required for database format")
            
            supported_drivers = ["postgresql", "mysql", "sqlite", "mssql"]
            if not any(driver in v.lower() for driver in supported_drivers):
                raise ValueError(
                    f"Unsupported database driver. Supported: {supported_drivers}"
                )
        return v


class DataGenerateResponse(BaseModel):
    """Response model for multiple table generation."""

    success: bool = Field(True, description="Whether the operation succeeded")
    data: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None, description="Generated data by table name (for JSON format)"
    )
    count: Dict[str, int] = Field(
        ..., description="Number of records generated per table"
    )
    tables_generated: int = Field(..., description="Number of tables generated")
    total_records: int = Field(..., description="Total records across all tables")
    format: str = Field(..., description="Format of the data")
    message: str = Field(
        "Multi-table data generated successfully", description="Status message"
    )
    
    # File export fields (for non-JSON formats)
    export_id: Optional[str] = Field(None, description="Export ID for file-based exports")
    filename: Optional[str] = Field(None, description="Generated filename")
    download_url: Optional[str] = Field(None, description="Download URL for files")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    expires_at: Optional[str] = Field(None, description="File expiration time")
    
    # Database export fields
    connection_summary: Optional[str] = Field(None, description="Masked connection string")
    tables_inserted: Optional[List[str]] = Field(None, description="Tables inserted to database")
    insert_time: Optional[str] = Field(None, description="Database insert timestamp")

