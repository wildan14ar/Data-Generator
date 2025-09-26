"""
Database seeding service
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import create_engine, Table, MetaData, exc
from sqlalchemy.engine import Engine

from app.core.exceptions import DatabaseError


logger = logging.getLogger(__name__)


def seed_db(data: List[Dict[str, Any]], conn_str: str, table: str, batch_size: int = 1000) -> None:
    """Seed database with generated data.
    
    Args:
        data: List of data records to insert
        conn_str: Database connection string (SQLAlchemy format)
        table: Target table name
        batch_size: Number of records to insert per batch
        
    Raises:
        DatabaseError: If database operation fails
    """
    if not data:
        logger.warning("No data to seed")
        return
    
    if not conn_str:
        raise DatabaseError("Connection string is required")
    
    if not table:
        raise DatabaseError("Table name is required")
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            conn_str,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False           # Set to True for SQL debugging
        )
        
        logger.info(f"Connecting to database: {engine.url.drivername}")
        
        # Test connection
        with engine.connect() as test_conn:
            test_conn.execute("SELECT 1")
        
        # Reflect database metadata
        meta = MetaData()
        meta.reflect(bind=engine)
        
        if table not in meta.tables:
            raise DatabaseError(f"Table '{table}' does not exist in database")
        
        tbl = meta.tables[table]
        logger.info(f"Target table: {table} with columns: {list(tbl.columns.keys())}")
        
        # Flatten data if needed and filter out columns not in table
        processed_data = []
        table_columns = set(tbl.columns.keys())
        
        for record in data:
            # Flatten nested structures
            flat_record = _flatten_dict_for_db(record)
            
            # Filter only columns that exist in the table
            filtered_record = {
                k: v for k, v in flat_record.items() 
                if k in table_columns
            }
            
            if filtered_record:  # Only add if we have valid columns
                processed_data.append(filtered_record)
        
        if not processed_data:
            logger.error("No valid data to insert after filtering")
            return
        
        # Insert data in batches
        total_inserted = 0
        with engine.begin() as conn:
            for i in range(0, len(processed_data), batch_size):
                batch = processed_data[i:i + batch_size]
                try:
                    result = conn.execute(tbl.insert(), batch)
                    batch_count = result.rowcount if hasattr(result, 'rowcount') else len(batch)
                    total_inserted += batch_count
                    logger.info(f"Inserted batch {i//batch_size + 1}: {batch_count} records")
                except Exception as e:
                    logger.error(f"Error inserting batch {i//batch_size + 1}: {e}")
                    raise DatabaseError(f"Error inserting batch: {e}")
        
        logger.info(f"✅ Successfully seeded {total_inserted} records into table '{table}'")
        
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database error: {e}")
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during seeding: {e}")
        raise DatabaseError(f"Unexpected error during seeding: {e}")
    finally:
        if 'engine' in locals():
            engine.dispose()


def _flatten_dict_for_db(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested dictionary for database insertion.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary with database-compatible values
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            # Recursively flatten nested objects
            items.extend(_flatten_dict_for_db(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert list to JSON string for database storage
            items.append((new_key, str(v) if v else None))
        else:
            items.append((new_key, v))
    
    return dict(items)


def test_connection(conn_str: str) -> bool:
    """Test database connection.
    
    Args:
        conn_str: Database connection string
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False