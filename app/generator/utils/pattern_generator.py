"""
Pattern generation utilities
"""

import random
import re
import logging
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()


def generate_pattern(pattern: str) -> str:
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


def generate_primary_key(model_name: str = None, field_name: str = None, schema: dict = None) -> str:
    """Generate unique primary key with format: 3-letter-prefix + '-' + 3-10 digit number.
    
    Args:
        model_name: Optional model/table name
        field_name: Optional field name (preferred for prefix)
        schema: Schema dictionary containing field information
        
    Returns:
        Generated primary key string
    """
    # Initialize primary key counter if not exists
    if not hasattr(generate_primary_key, '_pk_counter'):
        generate_primary_key._pk_counter = {}
    
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
    if counter_key not in generate_primary_key._pk_counter:
        generate_primary_key._pk_counter[counter_key] = 0
    
    generate_primary_key._pk_counter[counter_key] += 1
    counter = generate_primary_key._pk_counter[counter_key]
    
    # Generate random number with 3-10 digits
    random_digits = random.randint(3, 10)
    min_num = 10 ** (random_digits - 1)  # minimum number with required digits
    max_num = (10 ** random_digits) - 1   # maximum number with required digits
    
    # Add counter to ensure uniqueness even with same random number
    random_part = random.randint(min_num, max_num - counter) + counter
    
    return f"{prefix}-{random_part}"