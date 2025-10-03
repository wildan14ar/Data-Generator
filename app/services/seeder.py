"""
Database seeding service - Legacy compatibility layer
"""

# Import the new modular data manager functionality
from .handler import DatabaseSeeder, test_connection

# Legacy function for backward compatibility
def seed_db(data, conn_str, table, batch_size=1000):
    """Legacy seed_db function for backward compatibility."""
    seeder = DatabaseSeeder()
    result = seeder.seed(data, conn_str, table, batch_size)
    
    # Legacy function didn't return anything, just logged
    if not result["success"]:
        from app.config.exceptions import DatabaseError
        raise DatabaseError(result.get("error", "Seeding failed"))


# Re-export test_connection for compatibility
__all__ = ['seed_db', 'test_connection']