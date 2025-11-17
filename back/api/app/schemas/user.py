"""User schemas"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, UUID4

#
# ▼▼▼ [修正] ▼▼▼
# app.models.repo ではなく、正しいファイル名 'github_repo' からインポートします。
# これが 'ModuleNotFoundError' の修正です。
#
from app.models.github_repo import GitHubRepo


#
# ▼▼▼ [削除] ▼▼▼
# 'from app.schemas.user import ...' という
# 自分自身をインポートする（循環インポート）記述はすべて削除しました。
# これが 'ImportError' の修正です。
#


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
        # Pydantic v2.x
        from_attributes = True
        # Pydantic v1.x (もし古い場合)
        # orm_mode = True


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
        # orm_mode = True


class UserResponse(UserBase):
    """User response schema"""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        # orm_mode = True


class UserDetailResponse(UserResponse):
    """Detailed user response with skills and repos"""
    skills: List[UserSkillSchema] = []

    # ▼▼▼ [修正] ▼▼▼
    # GitHubRepoSchema を Pydantic v2 で正しく使うため、
    # 'repos' の型ヒントを 'List[GitHubRepoSchema]' にします。
    # (もし 'GitHubRepo' モデルを直接使おうとしていた場合の修正です)
    repos: List[GitHubRepoSchema] = []

    class Config:
        from_attributes = True
        # orm_mode = True


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]