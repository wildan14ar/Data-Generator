"""
Schema validation endpoints
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import SchemaValidationRequest, SchemaValidationResponse
from app.utils.validators import validate_schema, get_schema_features


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/validate", response_model=SchemaValidationResponse)
async def validate_schema_endpoint(request: SchemaValidationRequest):
    """Validate JSON schema."""
    try:
        schema = request.data_schema
        
        # Validate schema
        is_valid, errors, warnings = validate_schema(schema)
        
        # Get supported features
        supported_features = get_schema_features(schema)
        
        return SchemaValidationResponse(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            schema_type=schema.get('type'),
            supported_features=supported_features
        )
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Schema validation error: {str(e)}"
        )