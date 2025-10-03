"""
Database connection utilities
"""

import logging
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


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
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def mask_connection_string(conn_str: str) -> str:
    """Mask sensitive information in connection string.
    
    Args:
        conn_str: Connection string to mask
        
    Returns:
        Masked connection string
    """
    try:
        # Simple masking - hide password
        import re
        masked = re.sub(r'://[^:]+:[^@]+@', '://***:***@', conn_str)
        return masked
    except:
        return "***masked***"