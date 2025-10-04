"""
Reference type data generation
"""

import random
from typing import Dict, Any

from app.core.exceptions import GenerationError
from ..utils.cache_manager import get_ref_cache


def generate_reference(schema: Dict[str, Any]) -> Any:
    """Generate reference value based on schema.
    
    Args:
        schema: Reference schema dictionary
        
    Returns:
        Generated reference value
        
    Raises:
        GenerationError: If reference is invalid or not found
    """
    ref_str = schema.get("ref")
    if not ref_str:
        raise GenerationError("Reference schema harus memiliki property 'ref'")
        
    if "." not in ref_str:
        raise GenerationError(f"Invalid reference format: {ref_str}. Expected 'Model.field'")
        
    model, field = ref_str.split(".", 1)
    ref_cache = get_ref_cache()
    
    if model not in ref_cache:
        raise GenerationError(f"Model {model} belum tersedia untuk ref. Generate model {model} terlebih dahulu.")
    
    available_refs = [row[field] for row in ref_cache[model] if field in row]
    if not available_refs:
        raise GenerationError(f"Field {field} tidak ditemukan dalam model {model}")
        
    return random.choice(available_refs)