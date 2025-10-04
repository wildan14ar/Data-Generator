"""
Schema validation utilities
"""
import jsonschema
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_json_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that a JSON schema is properly formatted.
    
    Args:
        schema: JSON schema dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # Check basic structure
        if not isinstance(schema, dict):
            errors.append("Schema must be a dictionary")
            return False, errors
        
        # Check required top-level properties
        if "type" not in schema:
            errors.append("Schema must have a 'type' property")
        
        # Validate specific types
        schema_type = schema.get("type")
        
        if schema_type == "object":
            if "properties" not in schema:
                errors.append("Object schemas must have a 'properties' field")
            elif not isinstance(schema["properties"], dict):
                errors.append("'properties' must be a dictionary")
            
            # Validate each property
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if not isinstance(prop_schema, dict):
                    errors.append(f"Property '{prop_name}' must be a dictionary")
                elif "type" not in prop_schema:
                    errors.append(f"Property '{prop_name}' must have a 'type' field")
        
        elif schema_type == "array":
            if "items" not in schema:
                errors.append("Array schemas must have an 'items' field")
            elif not isinstance(schema["items"], dict):
                errors.append("'items' must be a dictionary")
        
        # Try to validate with jsonschema library if available

            try:
                jsonschema.Draft7Validator.check_schema(schema)
            except jsonschema.SchemaError as e:
                errors.append(f"JSON Schema validation error: {e.message}")
        else:
            logger.debug("jsonschema package not available, skipping advanced validation")
        
    except Exception as e:
        errors.append(f"Unexpected error during validation: {str(e)}")
    
    return len(errors) == 0, errors


def validate_database_schema(database_schema: Dict[str, Dict[str, Any]]) -> Tuple[bool, Dict[str, List[str]]]:
    """Validate a complete database schema.
    
    Args:
        database_schema: Dictionary with table names as keys and their schemas as values
        
    Returns:
        Tuple of (is_valid, dict_of_table_errors)
    """
    all_errors = {}
    is_valid = True
    
    if not isinstance(database_schema, dict):
        all_errors["_global"] = ["Database schema must be a dictionary"]
        return False, all_errors
    
    for table_name, table_schema in database_schema.items():
        table_valid, table_errors = validate_json_schema(table_schema)
        if not table_valid:
            all_errors[table_name] = table_errors
            is_valid = False
    
    return is_valid, all_errors


def check_foreign_key_references(database_schema: Dict[str, Dict[str, Any]]) -> List[str]:
    """Check that all foreign key references point to existing tables and columns.
    
    Args:
        database_schema: Dictionary with table names as keys and their schemas as values
        
    Returns:
        List of error messages for invalid foreign key references
    """
    errors = []
    
    # Get all tables and their primary keys
    table_columns = {}
    for table_name, table_schema in database_schema.items():
        properties = table_schema.get("properties", {})
        table_columns[table_name] = list(properties.keys())
    
    # Check foreign key references
    for table_name, table_schema in database_schema.items():
        properties = table_schema.get("properties", {})
        
        for col_name, col_schema in properties.items():
            foreign_key = col_schema.get("foreign_key")
            if foreign_key:
                ref_table = foreign_key.get("referenced_table")
                ref_column = foreign_key.get("referenced_column")
                
                # Check if referenced table exists
                if ref_table not in table_columns:
                    errors.append(
                        f"Table '{table_name}', column '{col_name}': "
                        f"references non-existent table '{ref_table}'"
                    )
                    continue
                
                # Check if referenced column exists
                if ref_column not in table_columns[ref_table]:
                    errors.append(
                        f"Table '{table_name}', column '{col_name}': "
                        f"references non-existent column '{ref_column}' in table '{ref_table}'"
                    )
    
    return errors


def normalize_table_name(table_name: str) -> str:
    """Normalize table name to follow database naming conventions.
    
    Args:
        table_name: Original table name
        
    Returns:
        Normalized table name
    """
    # Convert to lowercase
    normalized = table_name.lower()
    
    # Replace spaces and special characters with underscores
    import re
    normalized = re.sub(r'[^\w]', '_', normalized)
    
    # Remove multiple consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    # Ensure it starts with a letter
    if normalized and not normalized[0].isalpha():
        normalized = 'table_' + normalized
    
    return normalized


def normalize_column_name(column_name: str) -> str:
    """Normalize column name to follow database naming conventions.
    
    Args:
        column_name: Original column name
        
    Returns:
        Normalized column name
    """
    # Convert to lowercase
    normalized = column_name.lower()
    
    # Replace spaces and special characters with underscores
    import re
    normalized = re.sub(r'[^\w]', '_', normalized)
    
    # Remove multiple consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove leading/trailing underscores
    normalized = normalized.strip('_')
    
    # Ensure it starts with a letter or underscore
    if normalized and not (normalized[0].isalpha() or normalized[0] == '_'):
        normalized = 'col_' + normalized
    
    return normalized


def extract_schema_dependencies(database_schema: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract foreign key dependencies between tables.
    
    Args:
        database_schema: Dictionary with table names as keys and their schemas as values
        
    Returns:
        Dictionary mapping table names to their dependencies (tables they reference)
    """
    dependencies = {}
    
    for table_name, table_schema in database_schema.items():
        table_dependencies = set()
        properties = table_schema.get("properties", {})
        
        for col_schema in properties.values():
            foreign_key = col_schema.get("foreign_key")
            if foreign_key:
                ref_table = foreign_key.get("referenced_table")
                if ref_table and ref_table != table_name:  # Avoid self-references
                    table_dependencies.add(ref_table)
        
        dependencies[table_name] = list(table_dependencies)
    
    return dependencies


def get_creation_order(database_schema: Dict[str, Dict[str, Any]]) -> List[str]:
    """Determine the order in which tables should be created based on foreign key dependencies.
    
    Args:
        database_schema: Dictionary with table names as keys and their schemas as values
        
    Returns:
        List of table names in creation order
    """
    dependencies = extract_schema_dependencies(database_schema)
    
    # Topological sort to determine creation order
    creation_order = []
    remaining_tables = set(database_schema.keys())
    
    while remaining_tables:
        # Find tables with no remaining dependencies
        ready_tables = []
        for table in remaining_tables:
            table_deps = [dep for dep in dependencies[table] if dep in remaining_tables]
            if not table_deps:
                ready_tables.append(table)
        
        if not ready_tables:
            # Circular dependency or other issue - add remaining tables
            logger.warning("Circular dependency detected in schema, adding remaining tables")
            ready_tables = list(remaining_tables)
        
        # Add ready tables to creation order and remove from remaining
        ready_tables.sort()  # For consistent ordering
        creation_order.extend(ready_tables)
        remaining_tables -= set(ready_tables)
    
    return creation_order