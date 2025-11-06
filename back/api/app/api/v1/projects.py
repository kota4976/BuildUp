"""Project endpoints"""
import logging
from typing import Optional, TYPE_CHECKING
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.application import ApplicationCreate, ApplicationResponse
    from app.schemas.offer import OfferCreate, OfferResponse

from app.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.project import Project, ProjectSkill, Favorite
from app.models.skill import Skill
from app.models.audit import AuditLog
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectSkillResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project
    
    Args:
        project_data: Project creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created project
    """
    # Create project
    project = Project(
        owner_id=current_user.id,
        title=project_data.title,
        description=project_data.description,
        status="open"
    )
    db.add(project)
    db.flush()
    
    # Add required skills
    for skill_data in project_data.required_skills:
        # Verify skill exists
        skill = db.query(Skill).filter(Skill.id == skill_data.skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with id {skill_data.skill_id} not found"
            )
        
        # Validate level
        if skill_data.required_level < 1 or skill_data.required_level > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required level must be between 1 and 5"
            )
        
        project_skill = ProjectSkill(
            project_id=project.id,
            skill_id=skill_data.skill_id,
            required_level=skill_data.required_level
        )
        db.add(project_skill)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="CREATE_PROJECT",
        resource="projects",
        payload={"project_id": str(project.id), "title": project.title}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.from_orm(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    query: Optional[str] = Query(None, description="Search query for title/description"),
    skill_id: Optional[int] = Query(None, description="Filter by skill ID"),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    List projects with filters
    
    Args:
        query: Search query for title/description
        skill_id: Filter by skill
        owner_id: Filter by owner
        status: Filter by status
        limit: Maximum number of results
        offset: Offset for pagination
        current_user: Optional current user
        db: Database session
    
    Returns:
        List of projects
    """
    q = db.query(Project).options(
        joinedload(Project.project_skills).joinedload(ProjectSkill.skill)
    ).filter(Project.deleted_at.is_(None))
    
    # Apply filters
    if query:
        # Use PostgreSQL full-text search with unaccent_immutable function
        from sqlalchemy import text
        q = q.filter(
            text("to_tsvector('simple', unaccent_immutable(coalesce(projects.title, '') || ' ' || coalesce(projects.description, ''))) @@ plainto_tsquery('simple', :query)")
        ).params(query=query)
    
    if skill_id:
        q = q.join(ProjectSkill).filter(ProjectSkill.skill_id == skill_id)
    
    if owner_id:
        q = q.filter(Project.owner_id == owner_id)
    
    if status:
        q = q.filter(Project.status == status)
    
    # Get total count
    total = q.count()
    
    # Get projects
    projects = q.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()
    
    # Check if favorited by current user
    favorited_ids = set()
    if current_user:
        favorited_ids = set(
            fav.project_id for fav in db.query(Favorite).filter(
                Favorite.user_id == current_user.id,
                Favorite.project_id.in_([p.id for p in projects])
            ).all()
        )
    
    # Format response
    project_responses = []
    for project in projects:
        skills = [
            ProjectSkillResponse(
                skill_id=ps.skill_id,
                skill_name=ps.skill.name,
                required_level=ps.required_level
            )
            for ps in project.project_skills
        ]
        
        project_detail = ProjectDetailResponse.from_orm(project)
        project_detail.required_skills = skills
        project_detail.is_favorited = project.id in favorited_ids
        
        project_responses.append(project_detail)
    
    return ProjectListResponse(projects=project_responses, total=total)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get project by ID
    
    Args:
        project_id: Project ID
        current_user: Optional current user
        db: Database session
    
    Returns:
        Project detail
    """
    project = db.query(Project).options(
        joinedload(Project.project_skills).joinedload(ProjectSkill.skill)
    ).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if favorited
    is_favorited = False
    if current_user:
        is_favorited = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.project_id == project.id
        ).first() is not None
    
    # Format response
    skills = [
        ProjectSkillResponse(
            skill_id=ps.skill_id,
            skill_name=ps.skill.name,
            required_level=ps.required_level
        )
        for ps in project.project_skills
    ]
    
    project_detail = ProjectDetailResponse.from_orm(project)
    project_detail.required_skills = skills
    project_detail.is_favorited = is_favorited
    
    return project_detail


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update project
    
    Args:
        project_id: Project ID
        project_update: Project update data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated project
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    # Update fields
    if project_update.title is not None:
        project.title = project_update.title
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.status is not None:
        project.status = project_update.status
    
    # Update skills if provided
    if project_update.required_skills is not None:
        # Delete existing skills
        db.query(ProjectSkill).filter(
            ProjectSkill.project_id == project.id
        ).delete()
        
        # Add new skills
        for skill_data in project_update.required_skills:
            skill = db.query(Skill).filter(Skill.id == skill_data.skill_id).first()
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Skill with id {skill_data.skill_id} not found"
                )
            
            project_skill = ProjectSkill(
                project_id=project.id,
                skill_id=skill_data.skill_id,
                required_level=skill_data.required_level
            )
            db.add(project_skill)
    
    project.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="UPDATE_PROJECT",
        resource="projects",
        payload={"project_id": str(project.id)}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.from_orm(project)


@router.post("/{project_id}/favorite", response_model=SuccessResponse)
async def favorite_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add project to favorites
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Check if project exists
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if already favorited
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.project_id == project_id
    ).first()
    
    if existing:
        return SuccessResponse(message="Project already in favorites")
    
    # Add favorite
    favorite = Favorite(
        user_id=current_user.id,
        project_id=project_id
    )
    db.add(favorite)
    db.commit()
    
    return SuccessResponse(message="Project added to favorites")


@router.delete("/{project_id}/favorite", response_model=SuccessResponse)
async def unfavorite_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove project from favorites
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.project_id == project_id
    ).first()
    
    if not favorite:
        return SuccessResponse(message="Project not in favorites")
    
    db.delete(favorite)
    db.commit()
    
    return SuccessResponse(message="Project removed from favorites")


@router.post("/{project_id}/applications", status_code=status.HTTP_201_CREATED)
async def apply_to_project(
    project_id: str,
    application_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply to a project"""
    from app.models.application import Application
    from app.schemas.application import ApplicationCreate, ApplicationResponse
    
    # Parse request body
    application_data = ApplicationCreate(**application_data)
    
    # Check if project exists
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None),
        Project.status == "open"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not open"
        )
    
    # Cannot apply to own project
    if project.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply to your own project"
        )
    
    # Check if already applied
    existing = db.query(Application).filter(
        Application.project_id == project_id,
        Application.applicant_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already applied to this project"
        )
    
    # Create application
    application = Application(
        project_id=project_id,
        applicant_id=current_user.id,
        message=application_data.message,
        status="pending"
    )
    db.add(application)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="CREATE_APPLICATION",
        resource="applications",
        payload={"project_id": str(project_id)}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(application)
    
    return ApplicationResponse.from_orm(application)


@router.post("/{project_id}/offers", status_code=status.HTTP_201_CREATED)
async def create_offer(
    project_id: str,
    offer_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an offer to a user for a project"""
    from app.models.offer import Offer
    from app.schemas.offer import OfferCreate, OfferResponse
    
    # Parse request body
    offer_data = OfferCreate(**offer_data)
    
    # Check if project exists and user is owner
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None),
        Project.status == "open"
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not open"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can send offers"
        )
    
    # Check if receiver exists
    receiver = db.query(User).filter(
        User.id == offer_data.receiver_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot offer to self
    if receiver.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send offer to yourself"
        )
    
    # Check if already offered
    existing = db.query(Offer).filter(
        Offer.project_id == project_id,
        Offer.sender_id == current_user.id,
        Offer.receiver_id == offer_data.receiver_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer already sent to this user"
        )
    
    # Create offer
    offer = Offer(
        project_id=project_id,
        sender_id=current_user.id,
        receiver_id=offer_data.receiver_id,
        message=offer_data.message,
        status="pending"
    )
    db.add(offer)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="CREATE_OFFER",
        resource="offers",
        payload={"project_id": str(project_id), "receiver_id": str(offer_data.receiver_id)}
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(offer)
    
    return OfferResponse.from_orm(offer)

