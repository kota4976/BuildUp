"""Common schemas for request/response"""
from typing import Optional, Any, Dict
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail schema"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: ErrorDetail


class SuccessResponse(BaseModel):
    """Success response schema"""
    message: str
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = 20
    cursor: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    items: list
    next_cursor: Optional[str] = None
    has_more: bool = False

