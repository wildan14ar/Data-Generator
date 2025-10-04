"""
Database schema extraction service
"""

import logging
from typing import Dict, List, Any
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.config.exceptions import SchemaIntrospectionError, DatabaseError
from .converter import convert_table_to_json_schema


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
            schema = convert_table_to_json_schema(
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