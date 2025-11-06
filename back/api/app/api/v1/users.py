"""User endpoints"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.github_repo import GitHubRepo
from app.models.audit import AuditLog
from app.services.github_service import GitHubService
from app.schemas.user import (
    UserResponse,
    UserDetailResponse,
    UserUpdate,
    UserSkillUpdate,
    UserSkillSchema,
    GitHubRepoSchema
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user by ID with skills and repositories
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        User detail information
    """
    user = db.query(User).options(
        joinedload(User.user_skills).joinedload(UserSkill.skill),
        joinedload(User.github_repos)
    ).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Format response
    skills = [
        UserSkillSchema(
            skill_id=us.skill_id,
            skill_name=us.skill.name,
            level=us.level
        )
        for us in user.user_skills
    ]
    
    repos = [
        GitHubRepoSchema.from_orm(repo)
        for repo in user.github_repos
    ]
    
    user_response = UserDetailResponse.from_orm(user)
    user_response.skills = skills
    user_response.repos = repos
    
    return user_response


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated user information
    """
    # Update user fields
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    current_user.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="UPDATE_PROFILE",
        resource="users",
        payload=user_update.dict(exclude_unset=True)
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)


@router.put("/me/skills", response_model=SuccessResponse)
async def update_user_skills(
    skills: List[UserSkillUpdate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's skills
    
    Args:
        skills: List of skills with levels
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Delete existing skills
    db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id
    ).delete()
    
    # Add new skills
    for skill_data in skills:
        # Verify skill exists
        skill = db.query(Skill).filter(Skill.id == skill_data.skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with id {skill_data.skill_id} not found"
            )
        
        # Validate level
        if skill_data.level < 1 or skill_data.level > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill level must be between 1 and 5"
            )
        
        user_skill = UserSkill(
            user_id=current_user.id,
            skill_id=skill_data.skill_id,
            level=skill_data.level
        )
        db.add(user_skill)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="UPDATE_SKILLS",
        resource="users",
        payload={"skills": [s.dict() for s in skills]}
    )
    db.add(audit_log)
    
    db.commit()
    
    return SuccessResponse(message="Skills updated successfully")


@router.post("/me/repos/sync", response_model=SuccessResponse)
async def sync_github_repos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync GitHub repositories for current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Get OAuth account
    from app.models.user import OAuthAccount
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.user_id == current_user.id,
        OAuthAccount.provider == "github"
    ).first()
    
    if not oauth_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not linked"
        )
    
    try:
        # Fetch repos from GitHub
        repos = await GitHubService.get_user_repos(
            oauth_account.access_token,
            current_user.github_login
        )
        
        # Delete existing repos
        db.query(GitHubRepo).filter(
            GitHubRepo.user_id == current_user.id
        ).delete()
        
        # Add new repos
        for repo_data in repos:
            repo = GitHubRepo(
                user_id=current_user.id,
                repo_full_name=repo_data["full_name"],
                stars=repo_data.get("stargazers_count", 0),
                language=repo_data.get("language"),
                url=repo_data["html_url"],
                last_pushed_at=repo_data.get("pushed_at")
            )
            db.add(repo)
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action="SYNC_REPOS",
            resource="github_repos",
            payload={"repo_count": len(repos)}
        )
        db.add(audit_log)
        
        db.commit()
        
        return SuccessResponse(
            message=f"Successfully synced {len(repos)} repositories"
        )
        
    except Exception as e:
        logger.error(f"Failed to sync repos: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync repositories"
        )


@router.get("/me/applications")
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's applications"""
    from app.models.application import Application
    from app.schemas.application import ApplicationListResponse, ApplicationResponse
    
    applications = db.query(Application).filter(
        Application.applicant_id == current_user.id
    ).order_by(Application.created_at.desc()).all()
    
    return ApplicationListResponse(
        applications=[ApplicationResponse.from_orm(app) for app in applications]
    )


@router.get("/me/offers/sent")
async def get_sent_offers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get offers sent by current user"""
    from app.models.offer import Offer
    from app.schemas.offer import OfferListResponse, OfferResponse
    
    offers = db.query(Offer).filter(
        Offer.sender_id == current_user.id
    ).order_by(Offer.created_at.desc()).all()
    
    return OfferListResponse(
        offers=[OfferResponse.from_orm(offer) for offer in offers]
    )


@router.get("/me/offers/received")
async def get_received_offers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get offers received by current user"""
    from app.models.offer import Offer
    from app.schemas.offer import OfferListResponse, OfferResponse
    
    offers = db.query(Offer).filter(
        Offer.receiver_id == current_user.id
    ).order_by(Offer.created_at.desc()).all()
    
    return OfferListResponse(
        offers=[OfferResponse.from_orm(offer) for offer in offers]
    )

