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


def generate_sample(schema: Dict[str, Any], model_name: Optional[str] = None) -> Any:
    """Generate single value from schema.
    
    Args:
        schema: JSON schema dictionary
        model_name: Optional model name for referencing
        
    Returns:
        Generated value based on schema
        
    Raises:
        GenerationError: If schema is invalid or reference model not found
    """
    if not isinstance(schema, dict):
        raise GenerationError("Schema harus berupa dictionary")

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

        try:
            if fmt == "email":
                return fake.unique.email() if schema.get("unique") else fake.email()
            if fmt == "uuid":
                return str(fake.unique.uuid4()) if schema.get("unique") else str(fake.uuid4())
            if fmt == "date":
                return fake.date()
            if fmt == "name":
                return fake.name()
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
            generate_sample(schema["items"], model_name)
            for _ in range(count)
        ]

    # --- Object ---
    if t == "object":
        properties = schema.get("properties", {})
        if not properties:
            logger.warning("Object schema tidak memiliki properties")
            return {}
            
        return {
            key: generate_sample(sub_schema, model_name)
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


def generate_data(schema: Dict[str, Any], count: int, model_name: Optional[str] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Generate multiple data records from schema.
    
    Args:
        schema: JSON schema dictionary
        count: Number of records to generate
        model_name: Optional model name for referencing
        seed: Optional random seed for reproducible results
        
    Returns:
        List of generated data records
        
    Raises:
        GenerationError: If parameters are invalid
    """
    if count <= 0:
        raise GenerationError("Count harus lebih besar dari 0")
    
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)
        logger.info(f"Using seed: {seed}")

    logger.info(f"Generating {count} records{' for model ' + model_name if model_name else ''}")
    
    try:
        data = []
        for i in range(count):
            try:
                record = generate_sample(schema, model_name)
                data.append(record)
            except Exception as e:
                logger.error(f"Error generating record {i+1}: {e}")
                raise GenerationError(f"Error generating record {i+1}: {e}")
        
        if model_name:
            _ref_cache[model_name] = data
            logger.info(f"Cached {len(data)} records for model {model_name}")
            
        return data
        
    except GenerationError:
        raise
    except Exception as e:
        logger.error(f"Failed to generate data: {e}")
        raise GenerationError(f"Failed to generate data: {e}")