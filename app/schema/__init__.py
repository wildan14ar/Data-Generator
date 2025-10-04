"""
Schema module for database schema operations
"""

from .base import BaseSchema
from .types.extractor import (
    SchemaExtractor,
    get_database_tables,
    get_table_schema,
    get_database_schema
)
from .types.creator import (
    SchemaCreator,
    create_table_from_schema,
    create_database_from_schema,
    drop_table,
    drop_database_tables
)
from .types.converter import (
    SchemaConverter,
    convert_table_to_json_schema,
    sql_type_to_json_schema,
    json_schema_to_sql_type,
    generate_create_table_sql
)
from .utils.validation import (
    validate_json_schema,
    validate_database_schema,
    check_foreign_key_references,
    normalize_table_name,
    normalize_column_name,
    extract_schema_dependencies,
    get_creation_order
)
from .utils.formatter import (
    format_schema_for_display,
    compress_schema,
    extract_table_summary,
    extract_database_summary,
    merge_schemas,
    filter_schema_by_columns,
    rename_table_in_schema,
    rename_column_in_schema,
    convert_schema_to_openapi
)

__all__ = [
    # Main class
    'BaseSchema',
    
    # Service classes
    'SchemaExtractor',
    'SchemaCreator',
    'SchemaConverter',
    
    # Extractor functions (backward compatibility)
    'get_database_tables',
    'get_table_schema', 
    'get_database_schema',
    
    # Creator functions (backward compatibility)
    'create_table_from_schema',
    'create_database_from_schema',
    'drop_table',
    'drop_database_tables',
    
    # Converter functions (backward compatibility)
    'convert_table_to_json_schema',
    'sql_type_to_json_schema',
    'json_schema_to_sql_type',
    'generate_create_table_sql',
    
    # Validation utilities
    'validate_json_schema',
    'validate_database_schema',
    'check_foreign_key_references',
    'normalize_table_name',
    'normalize_column_name',
    'extract_schema_dependencies',
    'get_creation_order',
    
    # Formatting utilities
    'format_schema_for_display',
    'compress_schema',
    'extract_table_summary',
    'extract_database_summary',
    'merge_schemas',
    'filter_schema_by_columns',
    'rename_table_in_schema',
    'rename_column_in_schema',
    'convert_schema_to_openapi'
]