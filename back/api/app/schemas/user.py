"""User schemas"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, UUID4


class UserBase(BaseModel):
    """Base user schema"""
    handle: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    github_login: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    pass


class UserUpdate(BaseModel):
    """User update schema"""
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserSkillSchema(BaseModel):
    """User skill schema"""
    skill_id: int
    skill_name: str
    level: int
    
    class Config:
        from_attributes = True


class UserSkillUpdate(BaseModel):
    """User skill update schema"""
    skill_id: int
    level: int


class GitHubRepoSchema(BaseModel):
    """GitHub repository schema"""
    id: int
    repo_full_name: str
    stars: int
    language: Optional[str] = None
    url: str
    last_pushed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """User response schema"""
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response with skills and repos"""
    skills: List[UserSkillSchema] = []
    repos: List[GitHubRepoSchema] = []
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]

