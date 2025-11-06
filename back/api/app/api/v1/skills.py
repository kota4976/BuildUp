"""Skill endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillResponse, SkillListResponse

router = APIRouter()


@router.get("", response_model=SkillListResponse)
async def search_skills(
    query: Optional[str] = Query(None, description="Search query for skill names"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search skills by name (for autocomplete/suggestion)
    
    Args:
        query: Optional search query
        limit: Maximum number of results
        db: Database session
    
    Returns:
        List of matching skills
    """
    q = db.query(Skill)
    
    if query:
        # Case-insensitive partial match
        q = q.filter(Skill.name.ilike(f"%{query}%"))
    
    skills = q.order_by(Skill.name).limit(limit).all()
    
    return SkillListResponse(
        skills=[SkillResponse.from_orm(skill) for skill in skills]
    )

