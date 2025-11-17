"""Skill endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import SkillResponse, SkillListResponse, SkillCreate
from app.core.deps import get_current_user

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


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new skill (authenticated users only)
    
    Args:
        skill_data: Skill creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created skill
    
    Raises:
        HTTPException: If skill already exists or validation fails
    """
    # スキル名をトリムして正規化
    skill_name = skill_data.name.strip()
    
    # 空の名前をチェック
    if not skill_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="スキル名を入力してください"
        )
    
    # 長さチェック
    if len(skill_name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="スキル名は100文字以内で入力してください"
        )
    
    # 既存のスキルをチェック（大文字小文字を区別しない）
    existing_skill = db.query(Skill).filter(
        Skill.name.ilike(skill_name)
    ).first()
    
    if existing_skill:
        # 既に存在する場合は既存のスキルを返す
        return SkillResponse.from_orm(existing_skill)
    
    # 新しいスキルを作成
    new_skill = Skill(name=skill_name)
    
    try:
        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)
        return SkillResponse.from_orm(new_skill)
    except IntegrityError:
        db.rollback()
        # 競合状態で別のユーザーが同時に作成した場合
        existing_skill = db.query(Skill).filter(
            Skill.name.ilike(skill_name)
        ).first()
        if existing_skill:
            return SkillResponse.from_orm(existing_skill)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="スキルの作成に失敗しました"
        )

