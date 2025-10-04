"""
Schema module for database schema operations
"""

from .extractor import (
    get_database_tables,
    get_table_schema,
    get_database_schema
)
from .creator import (
    create_table_from_schema,
    create_database_from_schema,
    drop_table,
    drop_database_tables
)
from .converter import (
    sql_type_to_json_schema,
    json_schema_to_sql_type,
    convert_table_to_json_schema
)

__all__ = [
    # Extractor functions
    'get_database_tables',
    'get_table_schema', 
    'get_database_schema',
    
    # Creator functions
    'create_table_from_schema',
    'create_database_from_schema',
    'drop_table',
    'drop_database_tables',
    
    # Converter functions
    'sql_type_to_json_schema',
    'json_schema_to_sql_type',
    'convert_table_to_json_schema'
]