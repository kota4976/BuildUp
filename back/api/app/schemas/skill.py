"""Skill schemas"""
from typing import List
from pydantic import BaseModel


class SkillBase(BaseModel):
    """Base skill schema"""
    name: str


class SkillCreate(SkillBase):
    """Skill creation schema"""
    pass


class SkillResponse(SkillBase):
    """Skill response schema"""
    id: int
    
    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """Skill list response"""
    skills: List[SkillResponse]

