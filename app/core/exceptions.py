"""
Exception handlers and custom exceptions
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


class DatagenException(Exception):
    """Base exception for Datagen API."""
    pass


class GenerationError(DatagenException):
    """Exception raised during data generation."""
    pass


class ExportError(DatagenException):
    """Exception raised during data export."""
    pass


class DatabaseError(DatagenException):
    """Exception raised during database operations."""
    pass


class SchemaValidationError(DatagenException):
    """Exception raised during schema validation."""
    pass


def create_error_response(
    error_type: str,
    message: str,
    details: str = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error": message,
        "error_type": error_type,
        "details": details,
        "status_code": status_code
    }


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers."""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error_type="HTTPError",
                message=str(exc.detail),
                status_code=exc.status_code
            )
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=create_error_response(
                error_type="ValidationError",
                message="Request validation failed",
                details=str(exc.errors()),
                status_code=422
            )
        )
    
    @app.exception_handler(GenerationError)
    async def generation_exception_handler(request: Request, exc: GenerationError):
        """Handle data generation errors."""
        logger.error(f"Generation error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error_type="GenerationError",
                message=str(exc)
            )
        )
    
    @app.exception_handler(ExportError)
    async def export_exception_handler(request: Request, exc: ExportError):
        """Handle data export errors."""
        logger.error(f"Export error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error_type="ExportError",
                message=str(exc)
            )
        )
    
    @app.exception_handler(DatabaseError)
    async def database_exception_handler(request: Request, exc: DatabaseError):
        """Handle database errors."""
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error_type="DatabaseError",
                message=str(exc)
            )
        )
    
    @app.exception_handler(SchemaValidationError)
    async def schema_validation_exception_handler(request: Request, exc: SchemaValidationError):
        """Handle schema validation errors."""
        logger.error(f"Schema validation error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error_type="SchemaValidationError",
                message=str(exc)
            )
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                error_type="InternalServerError",
                message="An internal server error occurred",
                details=str(exc) if app.debug else None,
                status_code=500
            )
        )