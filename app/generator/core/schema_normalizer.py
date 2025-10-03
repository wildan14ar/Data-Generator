"""
Schema normalization utilities
"""

from typing import Dict, Any


def normalize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize schema from introspector format to generator format.
    
    Args:
        schema: JSON schema from introspector or generator format
        
    Returns:
        Normalized schema for generator
    """
    if not isinstance(schema, dict):
        return schema
    
    normalized = schema.copy()
    
    # Handle object schemas with title and description from introspector
    if schema.get("type") == "object":
        if "properties" in schema:
            # Recursively normalize properties
            normalized_props = {}
            for prop_name, prop_schema in schema["properties"].items():
                normalized_props[prop_name] = normalize_schema(prop_schema)
            normalized["properties"] = normalized_props
    
    # Handle array schemas
    elif schema.get("type") == "array" and "items" in schema:
        normalized["items"] = normalize_schema(schema["items"])
    
    # Remove introspector-specific metadata that generator doesn't need
    for key in ["title", "description"]:
        if key in normalized:
            del normalized[key]
    
    return normalized