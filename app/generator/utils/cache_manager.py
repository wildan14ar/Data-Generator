"""
Cache management for data generation
"""

from typing import Dict, Any, List
from faker import Faker

# Global caches
_unique_cache = {}  # cache untuk uniqueness
_ref_cache = {}     # cache untuk relasi antar model

fake = Faker()


def clear_caches():
    """Clear all internal caches."""
    global _unique_cache, _ref_cache
    _unique_cache.clear()
    _ref_cache.clear()
    fake.unique.clear()
    
    # Clear primary key counters
    if hasattr(get_ref_cache, '_pk_counter'):
        get_ref_cache._pk_counter.clear()


def get_ref_cache() -> Dict[str, List[Dict[str, Any]]]:
    """Get reference cache."""
    return _ref_cache


def set_ref_cache(model_name: str, data: List[Dict[str, Any]]):
    """Set reference cache for a model."""
    _ref_cache[model_name] = data


def get_unique_cache() -> Dict[str, Any]:
    """Get unique cache."""
    return _unique_cache


def set_unique_cache(key: str, value: Any):
    """Set unique cache value."""
    _unique_cache[key] = value