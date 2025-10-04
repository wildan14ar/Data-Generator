"""
Foreign type data generation
"""

import random
from typing import Dict, Any

from app.core.exceptions import GenerationError
from ..utils.cache_manager import get_ref_cache


def generate_foreign(schema: Dict[str, Any]) -> Any:
    """Generate foreign value based on schema.
    
    Args:
        schema: Foreign schema dictionary
        
    Returns:
        Generated foreign value
        
    Raises:
        GenerationError: If foreign ref is invalid or not found
    """
    ref_str = schema.get("ref")
    if not ref_str:
        raise GenerationError("Foreign schema harus memiliki property 'ref'")
        
    if "." not in ref_str:
        raise GenerationError(f"Invalid foreign format: {ref_str}. Expected 'Model.field'")
        
    model, field = ref_str.split(".", 1)
    ref_cache = get_ref_cache()
    
    if model not in ref_cache:
        raise GenerationError(f"Model {model} belum tersedia untuk foreign ref. Generate model {model} terlebih dahulu.")
    
    available_refs = [row[field] for row in ref_cache[model] if field in row]
    if not available_refs:
        raise GenerationError(f"Field {field} tidak ditemukan dalam model {model}")
        
    return random.choice(available_refs)
