"""
Object type data generation
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_object(schema: Dict[str, Any], generate_sample_func, model_name: Optional[str] = None, field_name: Optional[str] = None) -> Dict[str, Any]:
    """Generate object value based on schema.
    
    Args:
        schema: Object schema dictionary
        generate_sample_func: Function to generate individual properties
        model_name: Optional model name for referencing
        field_name: Optional field name for context
        
    Returns:
        Generated object value
    """
    properties = schema.get("properties", {})
    if not properties:
        logger.warning("Object schema tidak memiliki properties")
        return {}
        
    return {
        key: generate_sample_func(sub_schema, model_name, key)
        for key, sub_schema in properties.items()
    }