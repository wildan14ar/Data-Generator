"""
Schema conversion utilities between SQL and JSON Schema formats
"""

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def convert_table_to_json_schema(
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
        json_property = sql_type_to_json_schema(col_type, col_name, enum_values)

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


def sql_type_to_json_schema(sql_type: str, column_name: str, enum_values: Optional[List[str]] = None) -> Dict[str, Any]:
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


def json_schema_to_sql_type(json_property: Dict[str, Any], dialect: str = "postgresql") -> str:
    """Convert JSON Schema property to SQL data type.

    Args:
        json_property: JSON Schema property dictionary
        dialect: SQL dialect (postgresql, mysql, sqlite, etc.)

    Returns:
        SQL data type string
    """
    prop_type = json_property.get("type", "string")
    format_type = json_property.get("format")
    enum_values = json_property.get("enum")
    
    # Handle enum types
    if enum_values:
        if dialect.lower() == "postgresql":
            # PostgreSQL ENUM syntax
            enum_name = f"enum_{hash(str(enum_values)) % 1000000}"
            return f"CREATE TYPE {enum_name} AS ENUM ({', '.join(['\'{}\''.format(v) for v in enum_values])})"
        elif dialect.lower() == "mysql":
            # MySQL ENUM syntax
            return f"ENUM({', '.join(['\'{}\''.format(v) for v in enum_values])})"
        else:
            # Fallback to VARCHAR with check constraint
            return "VARCHAR(50)"
    
    # Handle different JSON Schema types
    if prop_type == "integer":
        if dialect.lower() == "postgresql":
            maximum = json_property.get("maximum", 2147483647)
            if maximum > 2147483647:
                return "BIGINT"
            elif maximum > 32767:
                return "INTEGER"
            else:
                return "SMALLINT"
        else:
            return "INT"
    
    elif prop_type == "number":
        if dialect.lower() == "postgresql":
            return "NUMERIC(10,2)"
        else:
            return "DECIMAL(10,2)"
    
    elif prop_type == "boolean":
        return "BOOLEAN"
    
    elif prop_type == "string":
        if format_type == "date":
            return "DATE"
        elif format_type == "datetime":
            return "TIMESTAMP"
        elif format_type == "email":
            return "VARCHAR(255)"
        elif format_type == "uuid":
            if dialect.lower() == "postgresql":
                return "UUID"
            else:
                return "VARCHAR(36)"
        elif format_type == "uri":
            return "VARCHAR(2048)"
        else:
            max_length = json_property.get("maxLength", 255)
            return f"VARCHAR({max_length})"
    
    elif prop_type == "array":
        if dialect.lower() == "postgresql":
            return "TEXT[]"
        else:
            return "JSON"
    
    elif prop_type == "object":
        if dialect.lower() in ["postgresql", "mysql"]:
            return "JSON"
        else:
            return "TEXT"
    
    # Default fallback
    return "VARCHAR(255)"


def generate_create_table_sql(table_name: str, json_schema: Dict[str, Any], dialect: str = "postgresql") -> str:
    """Generate CREATE TABLE SQL from JSON Schema.

    Args:
        table_name: Name of the table to create
        json_schema: JSON Schema dictionary
        dialect: SQL dialect (postgresql, mysql, sqlite, etc.)

    Returns:
        CREATE TABLE SQL statement
    """
    properties = json_schema.get("properties", {})
    required = json_schema.get("required", [])
    
    columns = []
    constraints = []
    
    for col_name, col_schema in properties.items():
        # Get SQL type
        sql_type = json_schema_to_sql_type(col_schema, dialect)
        
        # Build column definition
        column_def = f"{col_name} {sql_type}"
        
        # Add NOT NULL if required
        if col_name in required or col_schema.get("primary_key"):
            column_def += " NOT NULL"
        
        # Add PRIMARY KEY
        if col_schema.get("primary_key"):
            column_def += " PRIMARY KEY"
        
        # Add UNIQUE
        if col_schema.get("unique"):
            column_def += " UNIQUE"
        
        # Add DEFAULT
        if "default" in col_schema:
            default_val = col_schema["default"]
            if isinstance(default_val, str):
                column_def += f" DEFAULT '{default_val}'"
            else:
                column_def += f" DEFAULT {default_val}"
        
        columns.append(column_def)
        
        # Handle foreign keys
        if col_schema.get("foreign_key"):
            fk_info = col_schema["foreign_key"]
            constraint_name = f"fk_{table_name}_{col_name}"
            constraint = f"CONSTRAINT {constraint_name} FOREIGN KEY ({col_name}) REFERENCES {fk_info['referenced_table']}({fk_info['referenced_column']})"
            constraints.append(constraint)
    
    # Combine columns and constraints
    all_definitions = columns + constraints
    
    sql = f"CREATE TABLE {table_name} (\n"
    sql += ",\n".join(f"    {definition}" for definition in all_definitions)
    sql += "\n);"
    
    return sql