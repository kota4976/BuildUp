"""Authentication schemas"""
from pydantic import BaseModel
from app.schemas.user import UserResponse


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GitHubCallbackResponse(TokenResponse):
    """GitHub OAuth callback response"""
    pass

