"""Application schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, UUID4


class ApplicationCreate(BaseModel):
    """Application creation schema"""
    message: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Application response schema"""
    id: UUID4
    project_id: UUID4
    applicant_id: UUID4
    message: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """Application list response"""
    applications: list[ApplicationResponse]

