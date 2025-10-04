"""
Database schema creation service
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import ddl

from app.config.exceptions import SchemaIntrospectionError, DatabaseError
from .converter import generate_create_table_sql, json_schema_to_sql_type


logger = logging.getLogger(__name__)


def create_table_from_schema(
    connection_string: str, 
    table_name: str, 
    json_schema: Dict[str, Any],
    dialect: str = "postgresql",
    if_not_exists: bool = True
) -> bool:
    """Create a table in database from JSON Schema.

    Args:
        connection_string: Database connection string
        table_name: Name of the table to create
        json_schema: JSON Schema dictionary describing the table structure
        dialect: SQL dialect (postgresql, mysql, sqlite, etc.)
        if_not_exists: Whether to use IF NOT EXISTS clause

    Returns:
        True if table was created successfully, False if already exists

    Raises:
        SchemaIntrospectionError: If table creation fails
        DatabaseError: If database connection fails
    """
    try:
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Check if table already exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = :table_name
            """), {"table_name": table_name})
            
            table_exists = result.fetchone()[0] > 0
            
            if table_exists:
                if if_not_exists:
                    logger.info(f"Table '{table_name}' already exists, skipping creation")
                    return False
                else:
                    raise SchemaIntrospectionError(f"Table '{table_name}' already exists")
            
            # Generate CREATE TABLE SQL
            create_sql = generate_create_table_sql(table_name, json_schema, dialect)
            
            # Execute the SQL
            conn.execute(text(create_sql))
            conn.commit()
            
            logger.info(f"Successfully created table '{table_name}'")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Database error while creating table '{table_name}': {e}")
        raise DatabaseError(f"Database connection failed: {e}")
    except Exception as e:
        logger.error(f"Error creating table '{table_name}': {e}")
        raise SchemaIntrospectionError(f"Failed to create table: {e}")
    finally:
        engine.dispose()


def create_database_from_schema(
    connection_string: str, 
    database_schema: Dict[str, Dict[str, Any]],
    dialect: str = "postgresql",
    drop_existing: bool = False,
    create_order: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Create multiple tables in database from database schema.

    Args:
        connection_string: Database connection string
        database_schema: Dictionary with table names as keys and their schemas as values
        dialect: SQL dialect (postgresql, mysql, sqlite, etc.)
        drop_existing: Whether to drop existing tables before creating
        create_order: Optional list specifying order of table creation (for foreign key dependencies)

    Returns:
        Dictionary with table names as keys and creation success status as values

    Raises:
        SchemaIntrospectionError: If schema creation fails
        DatabaseError: If database connection fails
    """
    try:
        if drop_existing:
            drop_database_tables(connection_string, list(database_schema.keys()))
        
        # Determine creation order
        if create_order is None:
            # Simple ordering: tables without foreign keys first
            tables_with_fk = []
            tables_without_fk = []
            
            for table_name, schema in database_schema.items():
                has_foreign_key = any(
                    prop.get("foreign_key") is not None 
                    for prop in schema.get("properties", {}).values()
                )
                
                if has_foreign_key:
                    tables_with_fk.append(table_name)
                else:
                    tables_without_fk.append(table_name)
            
            create_order = tables_without_fk + tables_with_fk
        
        # Create tables in order
        results = {}
        for table_name in create_order:
            if table_name in database_schema:
                try:
                    success = create_table_from_schema(
                        connection_string, 
                        table_name, 
                        database_schema[table_name],
                        dialect,
                        if_not_exists=True
                    )
                    results[table_name] = success
                except Exception as e:
                    logger.warning(f"Failed to create table '{table_name}': {e}")
                    results[table_name] = False
                    # Continue with other tables
                    continue
        
        successful_tables = sum(1 for success in results.values() if success)
        logger.info(f"Successfully created {successful_tables} out of {len(database_schema)} tables")
        
        return results

    except Exception as e:
        logger.error(f"Error creating database schema: {e}")
        raise SchemaIntrospectionError(f"Failed to create database schema: {e}")


def drop_table(connection_string: str, table_name: str, if_exists: bool = True, cascade: bool = False) -> bool:
    """Drop a table from database.

    Args:
        connection_string: Database connection string
        table_name: Name of the table to drop
        if_exists: Whether to use IF EXISTS clause
        cascade: Whether to use CASCADE option

    Returns:
        True if table was dropped successfully, False if didn't exist

    Raises:
        SchemaIntrospectionError: If table dropping fails
        DatabaseError: If database connection fails
    """
    try:
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = :table_name
            """), {"table_name": table_name})
            
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                if if_exists:
                    logger.info(f"Table '{table_name}' does not exist, skipping drop")
                    return False
                else:
                    raise SchemaIntrospectionError(f"Table '{table_name}' does not exist")
            
            # Build DROP TABLE SQL
            drop_sql = f"DROP TABLE"
            if if_exists:
                drop_sql += " IF EXISTS"
            drop_sql += f" {table_name}"
            if cascade:
                drop_sql += " CASCADE"
            
            # Execute the SQL
            conn.execute(text(drop_sql))
            conn.commit()
            
            logger.info(f"Successfully dropped table '{table_name}'")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Database error while dropping table '{table_name}': {e}")
        raise DatabaseError(f"Database connection failed: {e}")
    except Exception as e:
        logger.error(f"Error dropping table '{table_name}': {e}")
        raise SchemaIntrospectionError(f"Failed to drop table: {e}")
    finally:
        engine.dispose()


def drop_database_tables(
    connection_string: str, 
    table_names: List[str], 
    if_exists: bool = True,
    cascade: bool = False
) -> Dict[str, bool]:
    """Drop multiple tables from database.

    Args:
        connection_string: Database connection string
        table_names: List of table names to drop
        if_exists: Whether to use IF EXISTS clause
        cascade: Whether to use CASCADE option

    Returns:
        Dictionary with table names as keys and drop success status as values

    Raises:
        SchemaIntrospectionError: If table dropping fails
        DatabaseError: If database connection fails
    """
    try:
        results = {}
        
        # Drop tables in reverse order to handle foreign key dependencies
        for table_name in reversed(table_names):
            try:
                success = drop_table(connection_string, table_name, if_exists, cascade)
                results[table_name] = success
            except Exception as e:
                logger.warning(f"Failed to drop table '{table_name}': {e}")
                results[table_name] = False
                # Continue with other tables
                continue
        
        successful_drops = sum(1 for success in results.values() if success)
        logger.info(f"Successfully dropped {successful_drops} out of {len(table_names)} tables")
        
        return results

    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise SchemaIntrospectionError(f"Failed to drop database tables: {e}")


def create_table_with_sqlalchemy(
    connection_string: str,
    table_name: str,
    json_schema: Dict[str, Any],
    metadata: Optional[MetaData] = None
) -> Table:
    """Create a table using SQLAlchemy ORM approach.

    Args:
        connection_string: Database connection string
        table_name: Name of the table to create
        json_schema: JSON Schema dictionary describing the table structure
        metadata: Optional SQLAlchemy MetaData object

    Returns:
        SQLAlchemy Table object

    Raises:
        SchemaIntrospectionError: If table creation fails
        DatabaseError: If database connection fails
    """
    try:
        engine = create_engine(connection_string)
        
        if metadata is None:
            metadata = MetaData()
        
        # Convert JSON Schema to SQLAlchemy columns
        columns = []
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])
        
        for col_name, col_schema in properties.items():
            # Determine SQLAlchemy column type
            col_type = _json_schema_to_sqlalchemy_type(col_schema)
            
            # Create column with constraints
            nullable = col_name not in required and not col_schema.get("primary_key", False)
            primary_key = col_schema.get("primary_key", False)
            unique = col_schema.get("unique", False)
            default = col_schema.get("default")
            
            # Handle foreign keys
            foreign_key = None
            if col_schema.get("foreign_key"):
                fk_info = col_schema["foreign_key"]
                foreign_key = ForeignKey(f"{fk_info['referenced_table']}.{fk_info['referenced_column']}")
            
            column = Column(
                col_name,
                col_type,
                nullable=nullable,
                primary_key=primary_key,
                unique=unique,
                default=default,
                *([foreign_key] if foreign_key else [])
            )
            
            columns.append(column)
        
        # Create table
        table = Table(table_name, metadata, *columns)
        
        # Create in database
        metadata.create_all(engine, tables=[table], checkfirst=True)
        
        logger.info(f"Successfully created table '{table_name}' using SQLAlchemy")
        return table

    except SQLAlchemyError as e:
        logger.error(f"Database error while creating table '{table_name}': {e}")
        raise DatabaseError(f"Database connection failed: {e}")
    except Exception as e:
        logger.error(f"Error creating table '{table_name}': {e}")
        raise SchemaIntrospectionError(f"Failed to create table: {e}")
    finally:
        engine.dispose()


def _json_schema_to_sqlalchemy_type(col_schema: Dict[str, Any]):
    """Convert JSON Schema property to SQLAlchemy column type.

    Args:
        col_schema: JSON Schema property dictionary

    Returns:
        SQLAlchemy column type
    """
    prop_type = col_schema.get("type", "string")
    format_type = col_schema.get("format")
    
    if prop_type == "integer":
        return Integer
    elif prop_type == "number":
        return Float
    elif prop_type == "boolean":
        return Boolean
    elif prop_type == "string":
        if format_type in ["date", "datetime"]:
            return DateTime
        else:
            max_length = col_schema.get("maxLength", 255)
            return String(max_length)
    else:
        # Default to String
        return String(255)