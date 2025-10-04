"""
Main schema management core functionality
"""

import logging
from typing import Dict, List, Any, Optional

from app.core.exceptions import SchemaIntrospectionError, DatabaseError
from .types.extractor import SchemaExtractor
from .types.creator import SchemaCreator
from .types.converter import SchemaConverter

logger = logging.getLogger(__name__)


class BaseSchema:
    """Core schema management class."""
    
    def __init__(self):
        """Initialize schema manager."""
        self.extractor = SchemaExtractor()
        self.creator = SchemaCreator()
        self.converter = SchemaConverter()
    
    def extract_database_schema(self, connection_string: str) -> Dict[str, Any]:
        """Extract schema information for entire database.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Dictionary with table names as keys and their schemas as values
            
        Raises:
            SchemaIntrospectionError: If introspection fails
            DatabaseError: If database connection fails
        """
        return self.extractor.get_database_schema(connection_string)
    
    def extract_table_schema(self, connection_string: str, table_name: str) -> Dict[str, Any]:
        """Extract schema information for a specific table.
        
        Args:
            connection_string: Database connection string
            table_name: Name of the table to introspect
            
        Returns:
            JSON Schema dictionary representing the table structure
            
        Raises:
            SchemaIntrospectionError: If introspection fails
            DatabaseError: If database connection fails
        """
        return self.extractor.get_table_schema(connection_string, table_name)
    
    def extract_database_tables(self, connection_string: str) -> List[str]:
        """Extract list of tables from database.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            List of table names
            
        Raises:
            SchemaIntrospectionError: If introspection fails
            DatabaseError: If database connection fails
        """
        return self.extractor.get_database_tables(connection_string)
    
    def create_table_from_schema(
        self,
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
        return self.creator.create_table_from_schema(
            connection_string, table_name, json_schema, dialect, if_not_exists
        )
    
    def create_database_from_schema(
        self,
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
            create_order: Optional list specifying order of table creation
            
        Returns:
            Dictionary with table names as keys and creation success status as values
            
        Raises:
            SchemaIntrospectionError: If schema creation fails
            DatabaseError: If database connection fails
        """
        return self.creator.create_database_from_schema(
            connection_string, database_schema, dialect, drop_existing, create_order
        )
    
    def drop_table(
        self, 
        connection_string: str, 
        table_name: str, 
        if_exists: bool = True, 
        cascade: bool = False
    ) -> bool:
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
        return self.creator.drop_table(connection_string, table_name, if_exists, cascade)
    
    def drop_database_tables(
        self,
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
        return self.creator.drop_database_tables(connection_string, table_names, if_exists, cascade)
    
    def convert_table_to_json_schema(
        self,
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
        return self.converter.convert_table_to_json_schema(
            table_name, columns, primary_keys, foreign_keys, unique_columns
        )
    
    def sql_type_to_json_schema(
        self, 
        sql_type: str, 
        column_name: str, 
        enum_values: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Convert SQL data type to JSON Schema property.
        
        Args:
            sql_type: SQL data type as string
            column_name: Column name for context
            enum_values: List of enum values if column is an enum type
            
        Returns:
            JSON Schema property dictionary
        """
        return self.converter.sql_type_to_json_schema(sql_type, column_name, enum_values)
    
    def json_schema_to_sql_type(
        self, 
        json_property: Dict[str, Any], 
        dialect: str = "postgresql"
    ) -> str:
        """Convert JSON Schema property to SQL data type.
        
        Args:
            json_property: JSON Schema property dictionary
            dialect: SQL dialect (postgresql, mysql, sqlite, etc.)
            
        Returns:
            SQL data type string
        """
        return self.converter.json_schema_to_sql_type(json_property, dialect)
    
    def generate_create_table_sql(
        self, 
        table_name: str, 
        json_schema: Dict[str, Any], 
        dialect: str = "postgresql"
    ) -> str:
        """Generate CREATE TABLE SQL from JSON Schema.
        
        Args:
            table_name: Name of the table to create
            json_schema: JSON Schema dictionary
            dialect: SQL dialect (postgresql, mysql, sqlite, etc.)
            
        Returns:
            CREATE TABLE SQL statement
        """
        return self.converter.generate_create_table_sql(table_name, json_schema, dialect)