"""
Pydantic models for API requests and responses
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    json = "json"
    csv = "csv" 
    sql = "sql"
    parquet = "parquet"


class GenerateRequest(BaseModel):
    """Request model for data generation."""
    data_schema: Dict[str, Any] = Field(..., description="JSON Schema for data generation", alias="schema")
    count: int = Field(10, ge=1, le=100000, description="Number of records to generate")
    model_name: Optional[str] = Field("Data", description="Model name for referencing")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    format: ExportFormat = Field(ExportFormat.json, description="Export format")
    
    class Config:
        populate_by_name = True
    
    @validator('data_schema')
    def validate_schema(cls, v):
        """Validate that schema has required properties."""
        if not isinstance(v, dict):
            raise ValueError("Schema must be a dictionary")
        if 'type' not in v:
            raise ValueError("Schema must have a 'type' property")
        return v


class GenerateMultiTableRequest(BaseModel):
    """Request model for generating multiple tables with relations."""
    schemas: Dict[str, Dict[str, Any]] = Field(..., description="Multiple table schemas (table_name -> schema)")
    count: Dict[str, int] = Field(..., description="Number of records per table (table_name -> count)")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    format: ExportFormat = Field(ExportFormat.json, description="Export format")
    
    @validator('schemas')
    def validate_schemas(cls, v):
        """Validate that all schemas are valid."""
        if not isinstance(v, dict):
            raise ValueError("Schemas must be a dictionary")
        
        for table_name, schema in v.items():
            if not isinstance(schema, dict):
                raise ValueError(f"Schema for table '{table_name}' must be a dictionary")
            if 'type' not in schema:
                raise ValueError(f"Schema for table '{table_name}' must have a 'type' property")
        
        return v
    
    @validator('count')
    def validate_count(cls, v, values):
        """Validate count matches schema tables."""
        schemas = values.get('schemas', {})
        if not isinstance(v, dict):
            raise ValueError("Count must be a dictionary")
        
        # Check all schemas have counts
        missing_counts = set(schemas.keys()) - set(v.keys())
        if missing_counts:
            raise ValueError(f"Missing count for tables: {missing_counts}")
        
        # Validate count values
        for table_name, count in v.items():
            if not isinstance(count, int) or count <= 0:
                raise ValueError(f"Count for table '{table_name}' must be a positive integer")
            if count > 100000:
                raise ValueError(f"Count for table '{table_name}' exceeds maximum limit (100000)")
        
        return v


class GenerateResponse(BaseModel):
    """Response model for data generation."""
    success: bool = Field(True, description="Whether the operation succeeded")
    data: List[Dict[str, Any]] = Field(..., description="Generated data")
    count: int = Field(..., description="Number of records generated")
    model_name: Optional[str] = Field(None, description="Model name used")
    seed: Optional[int] = Field(None, description="Seed used for generation")
    format: str = Field(..., description="Format of the data")
    message: str = Field("Data generated successfully", description="Status message")


class GenerateMultiTableResponse(BaseModel):
    """Response model for multiple table generation."""
    success: bool = Field(True, description="Whether the operation succeeded")
    data: Dict[str, List[Dict[str, Any]]] = Field(..., description="Generated data by table name")
    count: Dict[str, int] = Field(..., description="Number of records generated per table")
    tables_generated: int = Field(..., description="Number of tables generated")
    total_records: int = Field(..., description="Total records across all tables")
    seed: Optional[int] = Field(None, description="Seed used for generation")
    format: str = Field(..., description="Format of the data")
    message: str = Field("Multi-table data generated successfully", description="Status message")


class GenerateFileRequest(BaseModel):
    """Request model for generating data to file."""
    data_schema: Dict[str, Any] = Field(..., description="JSON Schema for data generation", alias="schema")
    count: int = Field(10, ge=1, le=100000, description="Number of records to generate")
    model_name: Optional[str] = Field("Data", description="Model name for referencing")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    format: ExportFormat = Field(ExportFormat.json, description="Export format")
    filename: str = Field(..., description="Output filename")
    table_name: Optional[str] = Field(None, description="Table name (required for SQL format)")
    
    class Config:
        populate_by_name = True
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Filename cannot be empty")
        return v.strip()
    
    @validator('table_name')
    def validate_table_name(cls, v, values):
        """Validate table name for SQL format."""
        if values.get('format') == ExportFormat.sql and not v:
            raise ValueError("Table name is required for SQL format")
        return v


class GenerateMultiTableFileRequest(BaseModel):
    """Request model for generating multiple tables to file."""
    schemas: Dict[str, Dict[str, Any]] = Field(..., description="Multiple table schemas (table_name -> schema)")
    count: Dict[str, int] = Field(..., description="Number of records per table (table_name -> count)")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    format: ExportFormat = Field(ExportFormat.json, description="Export format")
    filename: str = Field(..., description="Base filename (table names will be appended)")
    
    @validator('schemas')
    def validate_schemas(cls, v):
        """Validate that all schemas are valid."""
        if not isinstance(v, dict):
            raise ValueError("Schemas must be a dictionary")
        
        for table_name, schema in v.items():
            if not isinstance(schema, dict):
                raise ValueError(f"Schema for table '{table_name}' must be a dictionary")
            if 'type' not in schema:
                raise ValueError(f"Schema for table '{table_name}' must have a 'type' property")
        
        return v
    
    @validator('count')
    def validate_count(cls, v, values):
        """Validate count matches schema tables."""
        schemas = values.get('schemas', {})
        if not isinstance(v, dict):
            raise ValueError("Count must be a dictionary")
        
        # Check all schemas have counts
        missing_counts = set(schemas.keys()) - set(v.keys())
        if missing_counts:
            raise ValueError(f"Missing count for tables: {missing_counts}")
        
        # Validate count values
        for table_name, count in v.items():
            if not isinstance(count, int) or count <= 0:
                raise ValueError(f"Count for table '{table_name}' must be a positive integer")
            if count > 100000:
                raise ValueError(f"Count for table '{table_name}' exceeds maximum limit (100000)")
        
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Filename cannot be empty")
        return v.strip()


class SeedRequest(BaseModel):
    """Request model for database seeding."""
    data_schema: Dict[str, Any] = Field(..., description="JSON Schema for data generation", alias="schema")
    count: int = Field(10, ge=1, le=100000, description="Number of records to generate")
    model_name: Optional[str] = Field("Data", description="Model name for referencing")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    connection_string: str = Field(..., description="Database connection string")
    table_name: str = Field(..., description="Target table name")
    batch_size: int = Field(1000, ge=1, le=10000, description="Batch size for insertion")
    
    class Config:
        populate_by_name = True
    
    @validator('connection_string')
    def validate_connection_string(cls, v):
        """Validate connection string format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Connection string cannot be empty")
        
        supported_drivers = ['postgresql', 'mysql', 'sqlite', 'mssql']
        if not any(driver in v.lower() for driver in supported_drivers):
            raise ValueError(f"Unsupported database driver. Supported: {supported_drivers}")
        
        return v
    
    @validator('table_name')
    def validate_table_name(cls, v):
        """Validate table name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Table name cannot be empty")
        return v.strip()


class SeedResponse(BaseModel):
    """Response model for database seeding."""
    success: bool = Field(True, description="Whether the operation succeeded")
    records_inserted: int = Field(..., description="Number of records inserted")
    table_name: str = Field(..., description="Target table name")
    model_name: Optional[str] = Field(None, description="Model name used")
    seed: Optional[int] = Field(None, description="Seed used for generation")
    message: str = Field("Data seeded successfully", description="Status message")


class SchemaValidationRequest(BaseModel):
    """Request model for schema validation."""
    data_schema: Dict[str, Any] = Field(..., description="JSON Schema to validate", alias="schema")
    
    class Config:
        populate_by_name = True


class SchemaValidationResponse(BaseModel):
    """Response model for schema validation."""
    success: bool = Field(True, description="Whether validation succeeded")
    valid: bool = Field(..., description="Whether the schema is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    schema_type: Optional[str] = Field(None, description="Detected schema type")
    supported_features: List[str] = Field(default_factory=list, description="Supported features")


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
    popular_formats: Dict[str, int] = Field(default_factory=dict, description="Usage by format")
    average_generation_time: float = Field(0.0, description="Average generation time in seconds")
    uptime_hours: float = Field(0.0, description="Service uptime in hours")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    error_type: str = Field("GeneralError", description="Type of error")
    status_code: int = Field(400, description="HTTP status code")


# ============================================
# Database Schema Introspection Models
# ============================================

class DatabaseSchemaRequest(BaseModel):
    """Request model for getting database schema (multiple tables)."""
    connection_string: str = Field(..., description="Database connection string")
    tables: Optional[List[str]] = Field(None, description="Specific tables to introspect (if None, all tables)")
    
    @validator('connection_string')
    def validate_connection_string(cls, v):
        """Validate connection string format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Connection string cannot be empty")
        
        supported_drivers = ['postgresql', 'mysql', 'sqlite', 'mssql']
        if not any(driver in v.lower() for driver in supported_drivers):
            raise ValueError(f"Unsupported database driver. Supported: {supported_drivers}")
        
        return v

class DatabaseSchemaResponse(BaseModel):
    """Response model for database schema."""
    success: bool = Field(True, description="Whether the operation succeeded")
    schemas: Dict[str, Dict[str, Any]] = Field(..., description="Schema for each table")
    table_count: int = Field(..., description="Number of tables processed")
    message: str = Field("Database schema retrieved successfully", description="Status message")