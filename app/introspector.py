"""
Database schema introspection service
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config.exceptions import SchemaIntrospectionError, DatabaseError


logger = logging.getLogger(__name__)


def get_database_tables(connection_string: str) -> List[str]:
    """Get list of tables from database.

    Args:
        connection_string: Database connection string

    Returns:
        List of table names

    Raises:
        SchemaIntrospectionError: If introspection fails
        DatabaseError: If database connection fails
    """
    try:
        engine = create_engine(connection_string)

        with engine.connect():
            inspector = inspect(engine)
            tables = inspector.get_table_names()

        engine.dispose()
        logger.info(f"Found {len(tables)} tables in database")
        return sorted(tables)

    except SQLAlchemyError as e:
        logger.error(f"Database error while getting tables: {e}")
        raise DatabaseError(f"Database connection failed: {e}")
    except Exception as e:
        logger.error(f"Error getting database tables: {e}")
        raise SchemaIntrospectionError(f"Failed to get database tables: {e}")


def get_table_schema(connection_string: str, table_name: str) -> Dict[str, Any]:
    """Get schema information for a specific table.

    Args:
        connection_string: Database connection string
        table_name: Name of the table to introspect

    Returns:
        JSON Schema dictionary representing the table structure

    Raises:
        SchemaIntrospectionError: If introspection fails
        DatabaseError: If database connection fails
    """
    try:
        engine = create_engine(connection_string)

        with engine.connect():
            inspector = inspect(engine)

            # Check if table exists
            if table_name not in inspector.get_table_names():
                raise SchemaIntrospectionError(
                    f"Table '{table_name}' not found in database"
                )

            # Get columns information
            columns = inspector.get_columns(table_name)
            
            # Enhance columns with enum values if available
            for column in columns:
                if hasattr(column['type'], 'enums'):
                    # PostgreSQL ENUM type
                    column['enum_values'] = list(column['type'].enums)
                elif hasattr(column['type'], 'enum_class'):
                    # SQLAlchemy Enum type
                    column['enum_values'] = [e.value for e in column['type'].enum_class]
                elif str(column['type']).lower().startswith('enum'):
                    # MySQL ENUM type - extract values from type string
                    import re
                    enum_match = re.search(r"enum\('([^']+)'(?:,'([^']+)')*\)", str(column['type']).lower())
                    if enum_match:
                        # Extract all enum values from the match
                        enum_str = str(column['type'])
                        enum_values = re.findall(r"'([^']+)'", enum_str)
                        column['enum_values'] = enum_values

            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = (
                pk_constraint.get("constrained_columns", []) if pk_constraint else []
            )

            # Get foreign keys
            fk_constraints = inspector.get_foreign_keys(table_name)
            foreign_keys = {}
            for fk in fk_constraints:
                for col in fk["constrained_columns"]:
                    foreign_keys[col] = {
                        "referenced_table": fk["referred_table"],
                        "referenced_column": (
                            fk["referred_columns"][0]
                            if fk["referred_columns"]
                            else None
                        ),
                    }

            # Get unique constraints
            unique_constraints = inspector.get_unique_constraints(table_name)
            unique_columns = set()
            for constraint in unique_constraints:
                unique_columns.update(constraint.get("column_names", []))

            # Convert to JSON Schema
            schema = _convert_table_to_json_schema(
                table_name, columns, primary_keys, foreign_keys, unique_columns
            )

        engine.dispose()
        logger.info(f"Successfully generated schema for table '{table_name}'")
        return schema

    except SchemaIntrospectionError:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while introspecting table '{table_name}': {e}")
        raise DatabaseError(f"Database connection failed: {e}")
    except Exception as e:
        logger.error(f"Error introspecting table '{table_name}': {e}")
        raise SchemaIntrospectionError(f"Failed to introspect table schema: {e}")


def get_database_schema(connection_string: str) -> Dict[str, Any]:
    """Get schema information for entire database.

    Args:
        connection_string: Database connection string

    Returns:
        Dictionary with table names as keys and their schemas as values

    Raises:
        SchemaIntrospectionError: If introspection fails
        DatabaseError: If database connection fails
    """
    try:
        # Get available tables
        available_tables = get_database_tables(connection_string)

        if not available_tables:
            logger.warning("No tables found in database")
            return {}

        # Process all available tables
        tables_to_process = available_tables

        # Get schema for each table
        database_schema = {}
        for table_name in tables_to_process:
            try:
                table_schema = get_table_schema(connection_string, table_name)
                database_schema[table_name] = table_schema
            except Exception as e:
                logger.warning(f"Failed to get schema for table '{table_name}': {e}")
                # Continue with other tables
                continue

        logger.info(f"Successfully generated schema for {len(database_schema)} tables")
        return database_schema

    except SchemaIntrospectionError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        raise SchemaIntrospectionError(f"Failed to get database schema: {e}")


def _convert_table_to_json_schema(
    table_name: str,
    columns: List[Dict[str, Any]],
    primary_keys: List[str],
    foreign_keys: Dict[str, Dict[str, str]],
    unique_columns: set,
) -> Dict[str, Any]:
    """Convert SQLAlchemy table information to JSON Schema.

    Args:
        table_name: Name of the table
        columns: List of column information from SQLAlchemy inspector
        primary_keys: List of primary key column names
        foreign_keys: Dictionary mapping column names to foreign key info
        unique_columns: Set of unique column names

    Returns:
        JSON Schema dictionary
    """
    schema = {
        "type": "object",
        "title": table_name.title(),
        "description": f"Schema for table '{table_name}'",
        "properties": {},
        "required": [],
    }

    for column in columns:
        col_name = column["name"]
        col_type = str(column["type"]).lower()
        nullable = column.get("nullable", True)
        default = column.get("default")
        enum_values = column.get("enum_values")

        # Convert SQL types to JSON Schema types
        json_property = _sql_type_to_json_schema(col_type, col_name, enum_values)

        # Add constraints and metadata
        if not nullable and col_name not in primary_keys:
            schema["required"].append(col_name)

        if col_name in primary_keys:
            json_property["description"] = (
                f"Primary key - {json_property.get('description', '')}"
            )
            json_property["primary_key"] = True

        if col_name in foreign_keys:
            fk_info = foreign_keys[col_name]
            json_property["description"] = (
                f"Foreign key to {fk_info['referenced_table']}.{fk_info['referenced_column']} - {json_property.get('description', '')}"
            )
            json_property["foreign_key"] = fk_info
            json_property["type"] = "ref"
            json_property["ref"] = (
                f"{fk_info['referenced_table']}.{fk_info['referenced_column']}"
            )

        if col_name in unique_columns:
            json_property["unique"] = True

        if default is not None:
            json_property["default"] = str(default)

        schema["properties"][col_name] = json_property

    return schema


def _sql_type_to_json_schema(sql_type: str, column_name: str, enum_values: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convert SQL data type to JSON Schema property.

    Args:
        sql_type: SQL data type as string
        column_name: Column name for context
        enum_values: List of enum values if column is an enum type

    Returns:
        JSON Schema property dictionary
    """
    sql_type = sql_type.lower()

    # Handle ENUM types first
    if enum_values:
        return {
            "type": "string",
            "enum": enum_values,
            "description": f"Enum with values: {', '.join(enum_values)}"
        }
    
    # Check if type string contains enum pattern (fallback for databases that store enum as string)
    if "enum" in sql_type:
        import re
        # Try to extract enum values from type string like "enum('value1','value2')"
        enum_match = re.findall(r"'([^']+)'", sql_type)
        if enum_match:
            return {
                "type": "string",
                "enum": enum_match,
                "description": f"Enum with values: {', '.join(enum_match)}"
            }
        # If we can't extract values, treat as regular string with note
        return {
            "type": "string",
            "description": f"Enum type (values not extractable from: {sql_type})",
            "minLength": 1,
            "maxLength": 50
        }

    # Integer types
    if any(t in sql_type for t in ["integer", "int", "bigint", "smallint"]):
        schema = {"type": "integer"}
        if "id" in column_name.lower():
            schema.update({"minimum": 1, "maximum": 1000000})
        else:
            schema.update({"minimum": 1, "maximum": 1000})
        return schema

    # Float/Decimal types
    if any(t in sql_type for t in ["float", "double", "decimal", "numeric", "real"]):
        return {"type": "number", "minimum": 0.0, "maximum": 10000.0}

    # Boolean types
    if any(t in sql_type for t in ["boolean", "bool", "bit"]):
        return {"type": "boolean"}

    # Date/Time types
    if any(t in sql_type for t in ["date", "time", "timestamp"]):
        return {
            "type": "string",
            "format": "date" if "date" in sql_type else "datetime",
        }

    # String types
    if any(t in sql_type for t in ["varchar", "char", "text", "string"]):
        schema = {"type": "string"}

        # Determine format based on column name
        col_lower = column_name.lower()
        if "email" in col_lower:
            schema["format"] = "email"
            schema["unique"] = True
        elif "name" in col_lower or "title" in col_lower:
            schema["format"] = "name"
            schema.update({"minLength": 2, "maxLength": 50})
        elif "phone" in col_lower:
            schema["pattern"] = r"^\+?[\d\s\-\(\)]+$"
            schema.update({"minLength": 10, "maxLength": 20})
        elif "url" in col_lower or "link" in col_lower:
            schema["format"] = "uri"
        elif "uuid" in col_lower or "guid" in col_lower:
            schema["format"] = "uuid"
            schema["unique"] = True
        else:
            # Extract length from type if available
            import re

            length_match = re.search(r"\((\d+)\)", sql_type)
            if length_match:
                max_length = min(
                    int(length_match.group(1)), 100
                )  # Cap at 100 for generation
                schema.update({"minLength": 1, "maxLength": max_length})
            else:
                schema.update({"minLength": 3, "maxLength": 50})

        return schema

    # JSON/JSONB types
    if any(t in sql_type for t in ["json", "jsonb"]):
        return {
            "type": "object",
            "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
        }

    # Array types
    if "array" in sql_type:
        return {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3,
        }

    # Default to string
    return {
        "type": "string",
        "minLength": 3,
        "maxLength": 50,
        "description": f"Generated from SQL type: {sql_type}",
    }
