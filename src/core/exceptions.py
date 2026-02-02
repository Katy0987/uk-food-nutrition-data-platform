"""
Custom exceptions for the EcoAPI application.
Provides specific error types for better error handling.
"""

from typing import Any, Optional


class EcoAPIException(Exception):
    """Base exception for all EcoAPI errors."""
    
    def __init__(
        self,
        message: str,
        code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class DatabaseError(EcoAPIException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(message, code=500, details=details)


class CacheError(EcoAPIException):
    """Raised when cache operations fail."""
    
    def __init__(self, message: str = "Cache operation failed", details: Optional[Any] = None):
        super().__init__(message, code=500, details=details)


class ExternalAPIError(EcoAPIException):
    """Raised when external API calls fail."""
    
    def __init__(self, message: str = "External API request failed", details: Optional[Any] = None):
        super().__init__(message, code=502, details=details)


class NotFoundError(EcoAPIException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message, code=404, details=details)


class ValidationError(EcoAPIException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message, code=422, details=details)


class RateLimitError(EcoAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(message, code=429, details=details)


class ConfigurationError(EcoAPIException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration error", details: Optional[Any] = None):
        super().__init__(message, code=500, details=details)