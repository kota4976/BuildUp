"""Project schemas"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, UUID4


class ProjectSkillSchema(BaseModel):
    """Project skill requirement schema"""
    skill_id: int
    required_level: int


class ProjectSkillResponse(BaseModel):
    """Project skill with name"""
    skill_id: int
    skill_name: str
    required_level: int
    
    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    """Base project schema"""
    title: str
    description: str
    status: str = "open"


class ProjectCreate(BaseModel):
    """Project creation schema"""
    title: str
    description: str
    required_skills: List[ProjectSkillSchema] = []


class ProjectUpdate(BaseModel):
    """Project update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    required_skills: Optional[List[ProjectSkillSchema]] = None


from app.schemas.user import UserResponse


class ProjectResponse(ProjectBase):
    """Project response schema"""
    id: UUID4
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    owner: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with skills"""
    required_skills: List[ProjectSkillResponse] = []
    is_favorited: bool = False
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Project list response"""
    projects: List[ProjectDetailResponse]
    total: int

