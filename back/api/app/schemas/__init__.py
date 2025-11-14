"""Pydantic schemas for request/response"""
from app.schemas.common import ErrorResponse, ErrorDetail, SuccessResponse, PaginationParams, PaginatedResponse
from app.schemas.user import UserResponse, UserDetailResponse, UserUpdate, UserSkillUpdate
from app.schemas.auth import TokenResponse, GitHubCallbackResponse
from app.schemas.group_chat import (
    GroupConversationCreate, GroupConversationResponse, GroupConversationDetailResponse,
    GroupConversationUpdate, GroupMessageResponse, GroupMessageCreate,
    GroupMemberResponse, GroupMemberAdd, GroupMemberUpdateRole
)

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
    "GroupConversationCreate",
    "GroupConversationResponse",
    "GroupConversationDetailResponse",
    "GroupConversationUpdate",
    "GroupMessageResponse",
    "GroupMessageCreate",
    "GroupMemberResponse",
    "GroupMemberAdd",
    "GroupMemberUpdateRole",
]
