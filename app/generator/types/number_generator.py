"""
Number type data generation
"""

import random
from typing import Dict, Any, Union


def generate_number(schema: Dict[str, Any]) -> Union[int, float]:
    """Generate number value based on schema.
    
    Args:
        schema: Number schema dictionary
        field_name: Optional field name for context
        
    Returns:
        Generated number value (int or float)
    """
    t = schema.get("type")
    minimum = schema.get("minimum", 1)
    maximum = schema.get("maximum", 1000)
    
    if t == "integer":
        return random.randint(int(minimum), int(maximum))
    else:  # number (float)
        return round(random.uniform(float(minimum), float(maximum)), 2)