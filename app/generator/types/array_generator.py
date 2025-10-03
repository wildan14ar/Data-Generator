"""
Array type data generation
"""

import random
from typing import Dict, Any, List, Optional

from app.config.exceptions import GenerationError


def generate_array(schema: Dict[str, Any], generate_sample_func, model_name: Optional[str] = None, field_name: Optional[str] = None) -> List[Any]:
    """Generate array value based on schema.
    
    Args:
        schema: Array schema dictionary
        generate_sample_func: Function to generate individual items
        model_name: Optional model name for referencing
        field_name: Optional field name for context
        
    Returns:
        Generated array value
        
    Raises:
        GenerationError: If schema is invalid
    """
    if "items" not in schema:
        raise GenerationError("Array schema harus memiliki property 'items'")
        
    min_items = schema.get("minItems", 1)
    max_items = schema.get("maxItems", 3)
    count = random.randint(min_items, max_items)
    
    return [
        generate_sample_func(schema["items"], model_name, f"{field_name}_item" if field_name else None)
        for _ in range(count)
    ]