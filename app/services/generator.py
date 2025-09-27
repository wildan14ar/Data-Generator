"""
Data generation service
"""

import random
import re
import logging
from typing import Dict, List, Any, Optional
from faker import Faker

from app.core.exceptions import GenerationError


logger = logging.getLogger(__name__)

fake = Faker()
_unique_cache = {}  # cache untuk uniqueness
_ref_cache = {}     # cache untuk relasi antar model


def clear_caches():
    """Clear all internal caches."""
    global _unique_cache, _ref_cache
    _unique_cache.clear()
    _ref_cache.clear()
    fake.unique.clear()
    
    # Clear primary key counters
    if hasattr(generate_sample, '_pk_counter'):
        generate_sample._pk_counter.clear()
    
    # Clear primary key generation counters
    if hasattr(_generate_primary_key, '_pk_counter'):
        _generate_primary_key._pk_counter.clear()


def generate_sample(schema: Dict[str, Any], model_name: Optional[str] = None, field_name: Optional[str] = None) -> Any:
    """Generate single value from schema.
    
    Args:
        schema: JSON schema dictionary (supports both generator format and introspector format)
        model_name: Optional model name for referencing
        
    Returns:
        Generated value based on schema
        
    Raises:
        GenerationError: If schema is invalid or reference model not found
    """
    if not isinstance(schema, dict):
        raise GenerationError("Schema harus berupa dictionary")

    # --- Handle default values ---
    if "default" in schema and schema["default"] is not None:
        default_value = schema["default"]
        # Convert string representations back to proper types
        if schema.get("type") == "boolean":
            return str(default_value).lower() in ["true", "1", "yes"]
        elif schema.get("type") in ["integer", "number"]:
            try:
                return int(default_value) if schema.get("type") == "integer" else float(default_value)
            except (ValueError, TypeError):
                pass  # Fall through to generate random value
        return default_value

    # --- ENUM ---
    if "enum" in schema:
        return random.choice(schema["enum"])

    t = schema.get("type")
    if not t:
        raise GenerationError("Schema harus memiliki property 'type'")

    # --- String ---
    if t == "string":
        fmt = schema.get("format")
        min_len = schema.get("minLength", 3)
        max_len = schema.get("maxLength", 12)
        
        # Special handling for primary keys
        if schema.get("primary_key"):
            return _generate_primary_key(model_name, field_name, schema)

        try:
            if fmt == "email":
                return fake.unique.email() if schema.get("unique") else fake.email()
            if fmt == "uuid":
                return str(fake.unique.uuid4()) if schema.get("unique") else str(fake.uuid4())
            if fmt == "date":
                return fake.date()
            if fmt == "datetime":  # Support datetime format from introspector
                return fake.date_time().isoformat()
            if fmt == "name":
                return fake.name()
            if fmt == "uri":  # Support URI format from introspector
                return fake.url()
            if "pattern" in schema:
                return _generate_pattern(schema["pattern"])
            
            # Generate random word with length constraints
            word = fake.word()
            if len(word) > max_len:
                word = word[:max_len]
            elif len(word) < min_len:
                word = word + fake.word()[:min_len - len(word)]
            return word
            
        except Exception as e:
            logger.warning(f"Error generating string: {e}")
            return fake.word()[:max_len]

    # --- Integer/Number ---
    if t in ["integer", "number"]:
        minimum = schema.get("minimum", 1)
        maximum = schema.get("maximum", 1000)
        
        # Special handling for primary keys
        if schema.get("primary_key"):
            if t == "integer":
                # Generate auto-incrementing-like IDs for primary keys
                if not hasattr(generate_sample, '_pk_counter'):
                    generate_sample._pk_counter = {}
                table_key = f"{model_name or 'default'}_pk"
                if table_key not in generate_sample._pk_counter:
                    generate_sample._pk_counter[table_key] = 0
                generate_sample._pk_counter[table_key] += 1
                return generate_sample._pk_counter[table_key]
        
        if t == "integer":
            return random.randint(int(minimum), int(maximum))
        else:  # number (float)
            return round(random.uniform(float(minimum), float(maximum)), 2)

    # --- Boolean ---
    if t == "boolean":
        return random.choice([True, False])

    # --- Array ---
    if t == "array":
        if "items" not in schema:
            raise GenerationError("Array schema harus memiliki property 'items'")
            
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 3)
        count = random.randint(min_items, max_items)
        
        return [
            generate_sample(schema["items"], model_name, f"{field_name}_item" if field_name else None)
            for _ in range(count)
        ]

    # --- Object ---
    if t == "object":
        properties = schema.get("properties", {})
        if not properties:
            logger.warning("Object schema tidak memiliki properties")
            return {}
            
        return {
            key: generate_sample(sub_schema, model_name, key)
            for key, sub_schema in properties.items()
        }

    # --- Reference ---
    if t == "ref":
        ref_str = schema.get("ref")
        if not ref_str:
            raise GenerationError("Reference schema harus memiliki property 'ref'")
            
        if "." not in ref_str:
            raise GenerationError(f"Invalid reference format: {ref_str}. Expected 'Model.field'")
            
        model, field = ref_str.split(".", 1)
        if model not in _ref_cache:
            raise GenerationError(f"Model {model} belum tersedia untuk ref. Generate model {model} terlebih dahulu.")
        
        available_refs = [row[field] for row in _ref_cache[model] if field in row]
        if not available_refs:
            raise GenerationError(f"Field {field} tidak ditemukan dalam model {model}")
            
        return random.choice(available_refs)

    raise GenerationError(f"Unsupported schema type: {t}")


def _generate_primary_key(model_name: Optional[str], field_name: Optional[str], schema: Dict[str, Any]) -> str:
    """Generate unique primary key with format: 3-letter-prefix + '-' + 3-10 digit number.
    
    Args:
        model_name: Optional model/table name
        field_name: Optional field name (preferred for prefix)
        schema: Schema dictionary containing field information
        
    Returns:
        Generated primary key string
    """
    # Initialize primary key counter if not exists
    if not hasattr(_generate_primary_key, '_pk_counter'):
        _generate_primary_key._pk_counter = {}
    
    # Use field name as base for prefix, fallback to model name, then 'gen'
    if field_name:
        # Take first 3 characters of field name, lowercase
        prefix = field_name[:3].lower()
    elif model_name:
        # Take first 3 characters of model name, lowercase
        prefix = model_name[:3].lower()
    else:
        prefix = "gen"
    
    # Ensure prefix is exactly 3 characters
    if len(prefix) < 3:
        prefix = prefix.ljust(3, 'x')  # pad with 'x' if too short
    elif len(prefix) > 3:
        prefix = prefix[:3]
    
    # Generate unique counter for this prefix
    counter_key = f"{prefix}_pk"
    if counter_key not in _generate_primary_key._pk_counter:
        _generate_primary_key._pk_counter[counter_key] = 0
    
    _generate_primary_key._pk_counter[counter_key] += 1
    counter = _generate_primary_key._pk_counter[counter_key]
    
    # Generate random number with 3-10 digits
    random_digits = random.randint(3, 10)
    min_num = 10 ** (random_digits - 1)  # minimum number with required digits
    max_num = (10 ** random_digits) - 1   # maximum number with required digits
    
    # Add counter to ensure uniqueness even with same random number
    random_part = random.randint(min_num, max_num - counter) + counter
    
    return f"{prefix}-{random_part}"


def _generate_pattern(pattern: str) -> str:
    """Generate string matching simple regex patterns.
    
    Args:
        pattern: Simple regex pattern (limited support)
        
    Returns:
        Generated string matching pattern
    """
    try:
        # Handle simple patterns like [A-Z]{3}-[0-9]{4}
        result = pattern
        
        # Replace [A-Z]{n} with n random uppercase letters
        result = re.sub(r'\[A-Z\]\{(\d+)\}', lambda m: ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=int(m.group(1)))), result)
        
        # Replace [0-9]{n} with n random digits
        result = re.sub(r'\[0-9\]\{(\d+)\}', lambda m: ''.join(random.choices('0123456789', k=int(m.group(1)))), result)
        
        # Replace [a-z]{n} with n random lowercase letters
        result = re.sub(r'\[a-z\]\{(\d+)\}', lambda m: ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=int(m.group(1)))), result)
        
        # Simple single character classes
        result = re.sub(r'\[A-Z\]', lambda m: random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), result)
        result = re.sub(r'\[0-9\]', lambda m: random.choice('0123456789'), result)
        result = re.sub(r'\[a-z\]', lambda m: random.choice('abcdefghijklmnopqrstuvwxyz'), result)
        
        return result
    except Exception as e:
        logger.warning(f"Error generating pattern {pattern}: {e}")
        return fake.word()


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


def generate_data(
    schemas: Dict[str, Dict[str, Any]], 
    counts: Dict[str, int]
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate data for multiple related tables.
    
    Args:
        schemas: Dictionary of table_name -> schema
        counts: Dictionary of table_name -> count  
        
    Returns:
        Dictionary of table_name -> generated_data
        
    Raises:
        GenerationError: If generation fails
    """
    if not schemas:
        raise GenerationError("No schemas provided")
    
    if not counts:
        raise GenerationError("No counts provided")
    
    # Clear caches for fresh generation
    clear_caches()
    
    # Analyze dependencies to determine generation order
    generation_order = _determine_generation_order(schemas)
    logger.info(f"Generation order: {generation_order}")
    
    result = {}
    
    for table_name in generation_order:
        if table_name not in schemas:
            logger.warning(f"Skipping table '{table_name}' - schema not found")
            continue
            
        if table_name not in counts:
            logger.warning(f"Skipping table '{table_name}' - count not specified")
            continue
        
        table_schema = schemas[table_name]
        table_count = counts[table_name]
        
        try:
            logger.info(f"Generating {table_count} records for table '{table_name}'")
            
            # Normalize schema and generate data
            normalized_schema = normalize_schema(table_schema)
            table_data = []
            
            for i in range(table_count):
                try:
                    record = generate_sample(normalized_schema, table_name, None)
                    table_data.append(record)
                except Exception as e:
                    logger.error(f"Error generating record {i+1} for table '{table_name}': {e}")
                    raise GenerationError(f"Error generating record {i+1} for table '{table_name}': {e}")
            
            result[table_name] = table_data
            
            # Cache data for references
            _ref_cache[table_name] = table_data
            logger.info(f"Generated and cached {len(table_data)} records for table '{table_name}'")
            
        except GenerationError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate data for table '{table_name}': {e}")
            raise GenerationError(f"Failed to generate data for table '{table_name}': {e}")
    
    total_records = sum(len(data) for data in result.values())
    logger.info(f"Successfully generated {total_records} total records across {len(result)} tables")
    
    return result


def _determine_generation_order(schemas: Dict[str, Dict[str, Any]]) -> List[str]:
    """Determine the order to generate tables based on foreign key dependencies.
    
    Args:
        schemas: Dictionary of table schemas
        
    Returns:
        List of table names in dependency order (parents first)
    """
    # Build dependency graph
    dependencies = {}  # table -> set of tables it depends on
    
    for table_name, schema in schemas.items():
        dependencies[table_name] = set()
        
        if schema.get("type") == "object" and "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_schema.get("type") == "ref":
                    ref_str = prop_schema.get("ref", "")
                    if "." in ref_str:
                        referenced_table = ref_str.split(".", 1)[0]
                        if referenced_table in schemas:
                            dependencies[table_name].add(referenced_table)
    
    # Topological sort
    order = []
    visited = set()
    temp_visited = set()
    
    def visit(table: str):
        if table in temp_visited:
            logger.warning(f"Circular dependency detected involving table '{table}'")
            return
        if table in visited:
            return
        
        temp_visited.add(table)
        
        for dep in dependencies.get(table, set()):
            if dep in schemas:  # Only visit if dependency is in our schema set
                visit(dep)
        
        temp_visited.remove(table)
        visited.add(table)
        order.append(table)
    
    for table in schemas.keys():
        if table not in visited:
            visit(table)
    
    return order