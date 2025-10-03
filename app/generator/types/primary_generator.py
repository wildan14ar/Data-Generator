"""
Primary key data generation
"""

from typing import Dict, Any, Optional, Union
from ..utils.pattern_generator import generate_primary_key


def generate_primary(schema: Dict[str, Any], model_name: Optional[str] = None, field_name: Optional[str] = None) -> Union[int, str]:
    """Generate primary key value based on schema.
    
    Args:
        schema: Primary key schema dictionary
        model_name: Optional model name for referencing
        field_name: Optional field name for context
        
    Returns:
        Generated primary key value (int for integer type, str for string type)
    """
    t = schema.get("type", "string")
    
    if t == "integer":
        # Generate auto-incrementing-like IDs for integer primary keys
        if not hasattr(generate_primary, '_pk_counter'):
            generate_primary._pk_counter = {}
        table_key = f"{model_name or 'default'}_pk"
        if table_key not in generate_primary._pk_counter:
            generate_primary._pk_counter[table_key] = 0
        generate_primary._pk_counter[table_key] += 1
        return generate_primary._pk_counter[table_key]
    
    else:  # string type (default)
        # Generate string-based primary keys with pattern
        return generate_primary_key(model_name, field_name, schema)