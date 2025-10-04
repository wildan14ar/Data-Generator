"""
Schema utilities module
"""

from .validation import (
    validate_json_schema,
    validate_database_schema,
    check_foreign_key_references,
    normalize_table_name,
    normalize_column_name,
    extract_schema_dependencies,
    get_creation_order
)
from .formatter import (
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