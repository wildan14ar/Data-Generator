"""
Boolean type data generation
"""

import random
from typing import Dict, Any


def generate_boolean(schema: Dict[str, Any]) -> bool:
    """Generate boolean value.
    
    Args:
        schema: Boolean schema dictionary (unused but kept for consistency)
        
    Returns:
        Generated boolean value
    """
    return random.choice([True, False])