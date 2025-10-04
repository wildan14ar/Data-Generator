"""
String type data generation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from faker import Faker

from ..utils.pattern_generator import generate_pattern, generate_primary_key

logger = logging.getLogger(__name__)
fake = Faker()


def generate_string(schema: Dict[str, Any], model_name: Optional[str] = None, field_name: Optional[str] = None) -> str:
    """Generate string value based on schema.
    
    Args:
        schema: String schema dictionary
        model_name: Optional model name for referencing
        field_name: Optional field name for context
        
    Returns:
        Generated string value
    """
    fmt = schema.get("format")
    min_len = schema.get("minLength", 3)
    max_len = schema.get("maxLength", 12)

    # Special handling for date-related fields even if they don't have explicit format
    col_lower = (field_name or "").lower()
    if any(date_keyword in col_lower for date_keyword in ["date", "created", "updated", "birth", "expired", "start", "end", "time"]):
        # Generate date within 5 years back and forward from now (YYYY-MM-DD format only)
        current_date = datetime.now().date()
        start_date = current_date - timedelta(days=5*365)  # 5 years back
        end_date = current_date + timedelta(days=5*365)    # 5 years forward
        return fake.date_between(start_date=start_date, end_date=end_date).strftime('%Y-%m-%d')

    try:
        if fmt == "email":
            return fake.unique.email() if schema.get("unique") else fake.email()
        if fmt == "uuid":
            return str(fake.unique.uuid4()) if schema.get("unique") else str(fake.uuid4())
        if fmt == "date":
            # Generate date within 5 years back and forward from now (YYYY-MM-DD format only)
            current_date = datetime.now().date()
            start_date = current_date - timedelta(days=5*365)  # 5 years back
            end_date = current_date + timedelta(days=5*365)    # 5 years forward
            return fake.date_between(start_date=start_date, end_date=end_date).strftime('%Y-%m-%d')
        if fmt == "datetime":
            # Generate datetime within 5 years back and forward from now
            start_date = datetime.now() - timedelta(days=5*365)
            end_date = datetime.now() + timedelta(days=5*365)
            return fake.date_time_between(start_date=start_date, end_date=end_date).isoformat()
        if fmt == "name":
            return fake.name()
        if fmt == "uri":  # Support URI format from introspector
            return fake.url()
        if "pattern" in schema:
            return generate_pattern(schema["pattern"])
        
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
