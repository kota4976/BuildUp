"""Pydantic schemas for request/response"""
from app.schemas.common import ErrorResponse, ErrorDetail, SuccessResponse, PaginationParams, PaginatedResponse
from app.schemas.user import UserResponse, UserDetailResponse, UserUpdate, UserSkillUpdate
from app.schemas.auth import TokenResponse, GitHubCallbackResponse

__all__ = [
    "ErrorResponse",
    "ErrorDetail",
    "SuccessResponse",
    "PaginationParams",
    "PaginatedResponse",
    "UserResponse",
    "UserDetailResponse",
    "UserUpdate",
    "UserSkillUpdate",
    "TokenResponse",
    "GitHubCallbackResponse",
]
