"""
Database schema introspection endpoints
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    IntrospectTablesRequest, IntrospectTablesResponse,
    IntrospectTableSchemaRequest, IntrospectTableSchemaResponse,
    IntrospectDatabaseSchemaRequest, IntrospectDatabaseSchemaResponse
)
from app.services.introspector import (
    get_database_tables, get_table_schema, get_database_schema
)
from app.core.exceptions import SchemaIntrospectionError, DatabaseError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/introspect", tags=["Database Introspection"])


@router.post("/tables", response_model=IntrospectTablesResponse)
async def introspect_database_tables(request: IntrospectTablesRequest):
    """Get list of tables from database."""
    try:
        logger.info(f"Introspecting database tables")
        
        tables = get_database_tables(request.connection_string)
        
        return IntrospectTablesResponse(
            tables=tables,
            count=len(tables),
            message=f"Found {len(tables)} tables in database"
        )
        
    except DatabaseError as e:
        logger.error(f"Database error during table introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database connection failed: {str(e)}"
        )
    except SchemaIntrospectionError as e:
        logger.error(f"Introspection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during table introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during table introspection"
        )


@router.post("/table", response_model=IntrospectTableSchemaResponse)
async def introspect_table_schema(request: IntrospectTableSchemaRequest):
    """Get JSON Schema for a specific database table."""
    try:
        logger.info(f"Introspecting table schema for '{request.table_name}'")
        
        schema = get_table_schema(request.connection_string, request.table_name)
        
        # Extract metadata from schema
        properties = schema.get("properties", {})
        column_count = len(properties)
        primary_keys = [
            col_name for col_name, col_schema in properties.items() 
            if col_schema.get("primary_key", False)
        ]
        
        return IntrospectTableSchemaResponse(
            table_name=request.table_name,
            table_schema=schema,
            column_count=column_count,
            primary_keys=primary_keys,
            message=f"Schema retrieved successfully for table '{request.table_name}'"
        )
        
    except DatabaseError as e:
        logger.error(f"Database error during table schema introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database connection failed: {str(e)}"
        )
    except SchemaIntrospectionError as e:
        logger.error(f"Schema introspection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during table schema introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during table schema introspection"
        )


@router.post("/database", response_model=IntrospectDatabaseSchemaResponse)
async def introspect_database_schema(request: IntrospectDatabaseSchemaRequest):
    """Get JSON Schema for multiple tables or entire database."""
    try:
        tables_info = f"all tables" if not request.tables else f"tables: {', '.join(request.tables)}"
        logger.info(f"Introspecting database schema for {tables_info}")
        
        schemas = get_database_schema(request.connection_string, request.tables)
        
        return IntrospectDatabaseSchemaResponse(
            schemas=schemas,
            table_count=len(schemas),
            message=f"Database schema retrieved successfully for {len(schemas)} tables"
        )
        
    except DatabaseError as e:
        logger.error(f"Database error during database schema introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database connection failed: {str(e)}"
        )
    except SchemaIntrospectionError as e:
        logger.error(f"Schema introspection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during database schema introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during database schema introspection"
        )