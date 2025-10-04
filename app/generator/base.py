"""
Main data generation core functionality with schema normalization
"""

import random
import logging
from typing import Dict, List, Any, Optional

from app.core.exceptions import GenerationError
from .utils.cache_manager import clear_caches, get_ref_cache, set_ref_cache
from .utils.dependency_resolver import determine_generation_order
from .types.string_generator import generate_string
from .types.number_generator import generate_number
from .types.boolean_generator import generate_boolean
from .types.array_generator import generate_array
from .types.object_generator import generate_object
from .types.reference_generator import generate_reference
from .types.primary_generator import generate_primary

logger = logging.getLogger(__name__)

class BaseGenerator:
    """Core data generator class."""
    
    def __init__(self):
        pass

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


    def generate_sample(schema: Dict[str, Any], model_name: Optional[str] = None, field_name: Optional[str] = None) -> Any:
        """Generate single value from schema.
        
        Args:
            schema: JSON schema dictionary (supports both generator format and introspector format)
            model_name: Optional model name for referencing
            field_name: Optional field name for context
            
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

        # --- Primary Key ---
        if schema.get("primary_key"):
            return generate_primary(schema, model_name, field_name)

        # --- String ---
        if t == "string":
            return generate_string(schema, model_name, field_name)

        # --- Integer/Number ---
        if t in ["integer", "number"]:
            return generate_number(schema, model_name, field_name)

        # --- Boolean ---
        if t == "boolean":
            return generate_boolean(schema)

        # --- Array ---
        if t == "array":
            return generate_array(schema, generate_sample, model_name, field_name)

        # --- Object ---
        if t == "object":
            return generate_object(schema, generate_sample, model_name, field_name)

        # --- Reference ---
        if t == "ref":
            return generate_reference(schema)

        raise GenerationError(f"Unsupported schema type: {t}")


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
        generation_order = determine_generation_order(schemas)
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
                set_ref_cache(table_name, table_data)
                logger.info(f"Generated and cached {len(table_data)} records for table '{table_name}'")
                
            except GenerationError:
                raise
            except Exception as e:
                logger.error(f"Failed to generate data for table '{table_name}': {e}")
                raise GenerationError(f"Failed to generate data for table '{table_name}': {e}")
        
        total_records = sum(len(data) for data in result.values())
        logger.info(f"Successfully generated {total_records} total records across {len(result)} tables")
        
        return result