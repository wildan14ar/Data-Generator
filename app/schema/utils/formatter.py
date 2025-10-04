"""
Schema formatting and transformation utilities
"""

from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


def format_schema_for_display(schema: Dict[str, Any], indent: int = 2) -> str:
    """Format a JSON schema for human-readable display.
    
    Args:
        schema: JSON schema dictionary
        indent: Number of spaces for indentation
        
    Returns:
        Formatted schema string
    """
    try:
        return json.dumps(schema, indent=indent, sort_keys=True, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error formatting schema: {e}")
        return str(schema)


def compress_schema(schema: Dict[str, Any]) -> str:
    """Compress a JSON schema to a compact string representation.
    
    Args:
        schema: JSON schema dictionary
        
    Returns:
        Compressed schema string
    """
    try:
        return json.dumps(schema, separators=(',', ':'), ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error compressing schema: {e}")
        return str(schema)


def extract_table_summary(table_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a summary of a table schema.
    
    Args:
        table_schema: JSON schema for a table
        
    Returns:
        Dictionary with table summary information
    """
    summary = {
        "table_name": table_schema.get("title", "Unknown"),
        "description": table_schema.get("description", ""),
        "total_columns": 0,
        "required_columns": 0,
        "primary_keys": [],
        "foreign_keys": [],
        "unique_columns": [],
        "column_types": {}
    }
    
    properties = table_schema.get("properties", {})
    required = table_schema.get("required", [])
    
    summary["total_columns"] = len(properties)
    summary["required_columns"] = len(required)
    
    for col_name, col_schema in properties.items():
        # Track column types
        col_type = col_schema.get("type", "unknown")
        if col_type not in summary["column_types"]:
            summary["column_types"][col_type] = 0
        summary["column_types"][col_type] += 1
        
        # Track special columns
        if col_schema.get("primary_key"):
            summary["primary_keys"].append(col_name)
        
        if col_schema.get("foreign_key"):
            fk_info = col_schema["foreign_key"]
            summary["foreign_keys"].append({
                "column": col_name,
                "references": f"{fk_info['referenced_table']}.{fk_info['referenced_column']}"
            })
        
        if col_schema.get("unique"):
            summary["unique_columns"].append(col_name)
    
    return summary


def extract_database_summary(database_schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Extract a summary of the entire database schema.
    
    Args:
        database_schema: Dictionary with table names as keys and their schemas as values
        
    Returns:
        Dictionary with database summary information
    """
    summary = {
        "total_tables": len(database_schema),
        "total_columns": 0,
        "total_foreign_keys": 0,
        "tables": {},
        "column_type_distribution": {},
        "most_referenced_tables": {},
        "largest_tables": []
    }
    
    # Track table references
    table_references = {}
    
    for table_name, table_schema in database_schema.items():
        table_summary = extract_table_summary(table_schema)
        summary["tables"][table_name] = table_summary
        
        # Add to totals
        summary["total_columns"] += table_summary["total_columns"]
        summary["total_foreign_keys"] += len(table_summary["foreign_keys"])
        
        # Track column type distribution
        for col_type, count in table_summary["column_types"].items():
            if col_type not in summary["column_type_distribution"]:
                summary["column_type_distribution"][col_type] = 0
            summary["column_type_distribution"][col_type] += count
        
        # Track table references
        for fk in table_summary["foreign_keys"]:
            ref_table = fk["references"].split(".")[0]
            if ref_table not in table_references:
                table_references[ref_table] = 0
            table_references[ref_table] += 1
    
    # Find most referenced tables
    summary["most_referenced_tables"] = dict(
        sorted(table_references.items(), key=lambda x: x[1], reverse=True)[:5]
    )
    
    # Find largest tables (by column count)
    table_sizes = [(name, info["total_columns"]) for name, info in summary["tables"].items()]
    summary["largest_tables"] = sorted(table_sizes, key=lambda x: x[1], reverse=True)[:5]
    
    return summary


def merge_schemas(schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two JSON schemas, with schema2 taking precedence.
    
    Args:
        schema1: First schema (lower precedence)
        schema2: Second schema (higher precedence)
        
    Returns:
        Merged schema
    """
    merged = schema1.copy()
    
    for key, value in schema2.items():
        if key == "properties" and key in merged:
            # Merge properties
            merged_properties = merged["properties"].copy()
            merged_properties.update(value)
            merged["properties"] = merged_properties
        elif key == "required" and key in merged:
            # Merge required fields (union)
            merged["required"] = list(set(merged.get("required", []) + value))
        else:
            # Direct override
            merged[key] = value
    
    return merged


def filter_schema_by_columns(table_schema: Dict[str, Any], columns: List[str]) -> Dict[str, Any]:
    """Filter a table schema to include only specified columns.
    
    Args:
        table_schema: Original table schema
        columns: List of column names to include
        
    Returns:
        Filtered schema
    """
    filtered = table_schema.copy()
    
    # Filter properties
    if "properties" in filtered:
        filtered_properties = {
            col: schema for col, schema in filtered["properties"].items()
            if col in columns
        }
        filtered["properties"] = filtered_properties
    
    # Filter required fields
    if "required" in filtered:
        filtered["required"] = [
            col for col in filtered["required"] if col in columns
        ]
    
    return filtered


def rename_table_in_schema(table_schema: Dict[str, Any], old_name: str, new_name: str) -> Dict[str, Any]:
    """Rename a table in its schema definition.
    
    Args:
        table_schema: Table schema to modify
        old_name: Current table name
        new_name: New table name
        
    Returns:
        Modified schema with updated table name
    """
    modified = table_schema.copy()
    
    # Update title and description
    if modified.get("title") == old_name.title():
        modified["title"] = new_name.title()
    
    if "description" in modified:
        modified["description"] = modified["description"].replace(
            f"table '{old_name}'", f"table '{new_name}'"
        )
    
    return modified


def rename_column_in_schema(table_schema: Dict[str, Any], old_name: str, new_name: str) -> Dict[str, Any]:
    """Rename a column in a table schema.
    
    Args:
        table_schema: Table schema to modify
        old_name: Current column name
        new_name: New column name
        
    Returns:
        Modified schema with renamed column
    """
    modified = table_schema.copy()
    
    # Rename in properties
    if "properties" in modified and old_name in modified["properties"]:
        modified["properties"] = modified["properties"].copy()
        modified["properties"][new_name] = modified["properties"].pop(old_name)
    
    # Rename in required
    if "required" in modified and old_name in modified["required"]:
        modified["required"] = [
            new_name if col == old_name else col
            for col in modified["required"]
        ]
    
    return modified


def convert_schema_to_openapi(table_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a table schema to OpenAPI 3.0 schema format.
    
    Args:
        table_schema: JSON schema for a table
        
    Returns:
        OpenAPI-compatible schema
    """
    openapi_schema = {
        "type": "object",
        "properties": {},
        "required": table_schema.get("required", [])
    }
    
    if "title" in table_schema:
        openapi_schema["title"] = table_schema["title"]
    
    if "description" in table_schema:
        openapi_schema["description"] = table_schema["description"]
    
    properties = table_schema.get("properties", {})
    
    for col_name, col_schema in properties.items():
        openapi_prop = {
            "type": col_schema.get("type", "string")
        }
        
        # Copy common properties
        for prop in ["description", "example", "default", "enum", "format"]:
            if prop in col_schema:
                openapi_prop[prop] = col_schema[prop]
        
        # Handle string constraints
        if col_schema.get("type") == "string":
            for prop in ["minLength", "maxLength", "pattern"]:
                if prop in col_schema:
                    openapi_prop[prop] = col_schema[prop]
        
        # Handle number constraints
        elif col_schema.get("type") in ["integer", "number"]:
            for prop in ["minimum", "maximum", "multipleOf"]:
                if prop in col_schema:
                    openapi_prop[prop] = col_schema[prop]
        
        # Handle array constraints
        elif col_schema.get("type") == "array":
            for prop in ["minItems", "maxItems", "items"]:
                if prop in col_schema:
                    openapi_prop[prop] = col_schema[prop]
        
        openapi_schema["properties"][col_name] = openapi_prop
    
    return openapi_schema