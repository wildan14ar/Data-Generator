"""
Schema validation utilities
"""

import logging
from typing import Dict, Any, List, Tuple

from app.config.exceptions import SchemaValidationError


logger = logging.getLogger(__name__)


def validate_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """Validate JSON schema for data generation.
    
    Args:
        schema: JSON schema dictionary
        
    Returns:
        Tuple of (is_valid, errors, warnings)
        
    Raises:
        SchemaValidationError: If schema is completely invalid
    """
    if not isinstance(schema, dict):
        raise SchemaValidationError("Schema must be a dictionary")
    
    errors = []
    warnings = []
    
    # Check required properties
    if 'type' not in schema:
        errors.append("Schema must have a 'type' property")
        return False, errors, warnings
    
    schema_type = schema.get('type')
    
    # Validate based on type
    if schema_type == 'object':
        _validate_object_schema(schema, errors, warnings)
    elif schema_type == 'array':
        _validate_array_schema(schema, errors, warnings)
    elif schema_type == 'string':
        _validate_string_schema(schema, errors, warnings)
    elif schema_type in ['integer', 'number']:
        _validate_number_schema(schema, errors, warnings)
    elif schema_type == 'boolean':
        pass  # Boolean schema is always valid
    elif schema_type == 'ref':
        _validate_ref_schema(schema, errors, warnings)
    else:
        errors.append(f"Unsupported schema type: {schema_type}")
    
    # Check for enum
    if 'enum' in schema:
        _validate_enum_schema(schema, errors, warnings)
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def _validate_object_schema(schema: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate object schema."""
    if 'properties' not in schema:
        warnings.append("Object schema without properties may generate empty objects")
    else:
        properties = schema['properties']
        if not isinstance(properties, dict):
            errors.append("Object properties must be a dictionary")
        else:
            for prop_name, prop_schema in properties.items():
                try:
                    is_valid, prop_errors, prop_warnings = validate_schema(prop_schema)
                    for error in prop_errors:
                        errors.append(f"Property '{prop_name}': {error}")
                    for warning in prop_warnings:
                        warnings.append(f"Property '{prop_name}': {warning}")
                except Exception as e:
                    errors.append(f"Property '{prop_name}': {str(e)}")


def _validate_array_schema(schema: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate array schema."""
    if 'items' not in schema:
        errors.append("Array schema must have an 'items' property")
    else:
        try:
            is_valid, item_errors, item_warnings = validate_schema(schema['items'])
            for error in item_errors:
                errors.append(f"Array items: {error}")
            for warning in item_warnings:
                warnings.append(f"Array items: {warning}")
        except Exception as e:
            errors.append(f"Array items: {str(e)}")
    
    # Validate size constraints
    min_items = schema.get('minItems')
    max_items = schema.get('maxItems')
    
    if min_items is not None and not isinstance(min_items, int):
        errors.append("minItems must be an integer")
    elif min_items is not None and min_items < 0:
        errors.append("minItems must be non-negative")
    
    if max_items is not None and not isinstance(max_items, int):
        errors.append("maxItems must be an integer")
    elif max_items is not None and max_items < 0:
        errors.append("maxItems must be non-negative")
    
    if min_items is not None and max_items is not None and min_items > max_items:
        errors.append("minItems must be less than or equal to maxItems")


def _validate_string_schema(schema: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate string schema."""
    format_val = schema.get('format')
    pattern = schema.get('pattern')
    min_length = schema.get('minLength')
    max_length = schema.get('maxLength')
    
    # Validate format
    if format_val is not None:
        supported_formats = ['email', 'uuid', 'date', 'name']
        if format_val not in supported_formats:
            warnings.append(f"Format '{format_val}' may not be supported. Supported: {supported_formats}")
    
    # Validate pattern
    if pattern is not None:
        try:
            import re
            re.compile(pattern)
        except re.error as e:
            warnings.append(f"Invalid regex pattern: {e}")
    
    # Validate length constraints
    if min_length is not None and not isinstance(min_length, int):
        errors.append("minLength must be an integer")
    elif min_length is not None and min_length < 0:
        errors.append("minLength must be non-negative")
    
    if max_length is not None and not isinstance(max_length, int):
        errors.append("maxLength must be an integer")
    elif max_length is not None and max_length < 0:
        errors.append("maxLength must be non-negative")
    
    if min_length is not None and max_length is not None and min_length > max_length:
        errors.append("minLength must be less than or equal to maxLength")


def _validate_number_schema(schema: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate number/integer schema."""
    minimum = schema.get('minimum')
    maximum = schema.get('maximum')
    schema_type = schema.get('type')
    
    if minimum is not None and not isinstance(minimum, (int, float)):
        errors.append("minimum must be a number")
    
    if maximum is not None and not isinstance(maximum, (int, float)):
        errors.append("maximum must be a number")
    
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append("minimum must be less than or equal to maximum")
    
    # Type-specific validation
    if schema_type == 'integer':
        if minimum is not None and not isinstance(minimum, int):
            warnings.append("minimum should be an integer for integer type")
        if maximum is not None and not isinstance(maximum, int):
            warnings.append("maximum should be an integer for integer type")


def _validate_ref_schema(schema: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate reference schema."""
    ref = schema.get('ref')
    if not ref:
        errors.append("Reference schema must have a 'ref' property")
    elif not isinstance(ref, str):
        errors.append("Reference 'ref' must be a string")
    elif '.' not in ref:
        errors.append("Reference must be in format 'Model.field'")
    else:
        model, field = ref.split('.', 1)
        if not model or not field:
            errors.append("Both model and field names must be non-empty in reference")


def _validate_enum_schema(schema: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate enum schema."""
    enum_values = schema['enum']
    if not isinstance(enum_values, list):
        errors.append("enum must be a list")
    elif len(enum_values) == 0:
        errors.append("enum must have at least one value")


def get_schema_features(schema: Dict[str, Any]) -> List[str]:
    """Get list of features used in schema.
    
    Args:
        schema: JSON schema dictionary
        
    Returns:
        List of feature names
    """
    features = set()
    
    def _scan_schema(s: Dict[str, Any]):
        if not isinstance(s, dict):
            return
        
        # Check for enum
        if 'enum' in s:
            features.add('enums')
        
        # Check for string formats
        if s.get('type') == 'string' and 'format' in s:
            features.add('string_formats')
        
        # Check for patterns
        if 'pattern' in s:
            features.add('regex_patterns')
        
        # Check for references
        if s.get('type') == 'ref':
            features.add('references')
        
        # Check for uniqueness
        if s.get('unique'):
            features.add('uniqueness')
        
        # Check for constraints
        if any(key in s for key in ['minimum', 'maximum', 'minLength', 'maxLength', 'minItems', 'maxItems']):
            features.add('constraints')
        
        # Recursively check nested schemas
        if s.get('type') == 'object' and 'properties' in s:
            for prop_schema in s['properties'].values():
                _scan_schema(prop_schema)
        elif s.get('type') == 'array' and 'items' in s:
            _scan_schema(s['items'])
    
    _scan_schema(schema)
    return list(features)