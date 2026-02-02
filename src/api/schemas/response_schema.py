"""
Standard response schemas for API endpoints.
Ensures consistent response format across all endpoints.
"""

from typing import Any, Optional, Dict, List, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class Meta(BaseModel):
    """Metadata for API responses."""
    count: Optional[int] = Field(None, description="Number of items in response")
    limit: Optional[int] = Field(None, description="Limit applied to query")
    offset: Optional[int] = Field(None, description="Offset applied to query")
    total: Optional[int] = Field(None, description="Total items available")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    cached: Optional[bool] = Field(None, description="Whether response was cached")
    
    class Config:
        extra = "allow"  # Allow additional fields


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    details: Optional[Any] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standard success response wrapper.
    
    Example:
        {
            "success": true,
            "data": {...},
            "meta": {
                "count": 10,
                "response_time_ms": 245
            }
        }
    """
    success: bool = Field(True, description="Success status")
    data: T = Field(..., description="Response data")
    meta: Optional[Meta] = Field(None, description="Response metadata")


class ErrorResponse(BaseModel):
    """
    Standard error response wrapper.
    
    Example:
        {
            "success": false,
            "error": {
                "code": 404,
                "message": "Resource not found",
                "type": "not_found_error"
            }
        }
    """
    success: bool = Field(False, description="Success status")
    error: ErrorDetail = Field(..., description="Error details")


class ListResponse(BaseModel, Generic[T]):
    """
    Standard list response wrapper.
    
    Example:
        {
            "success": true,
            "data": [...],
            "meta": {
                "count": 10,
                "total": 100,
                "limit": 20,
                "offset": 0
            }
        }
    """
    success: bool = Field(True, description="Success status")
    data: List[T] = Field(..., description="List of items")
    meta: Optional[Meta] = Field(None, description="List metadata")


# Convenience functions for creating responses

def success_response(
    data: Any,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a success response."""
    response = {
        "success": True,
        "data": data
    }
    if meta:
        response["meta"] = meta
    return response


def error_response(
    code: int,
    message: str,
    error_type: str = "error",
    details: Any = None
) -> Dict[str, Any]:
    """Create an error response."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "type": error_type,
            "details": details
        }
    }


def list_response(
    data: List[Any],
    count: Optional[int] = None,
    total: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a list response with metadata."""
    meta = {
        "count": count if count is not None else len(data),
    }
    if total is not None:
        meta["total"] = total
    if limit is not None:
        meta["limit"] = limit
    if offset is not None:
        meta["offset"] = offset
    
    # Add any additional metadata
    meta.update(kwargs)
    
    return {
        "success": True,
        "data": data,
        "meta": meta
    }