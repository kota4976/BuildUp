"""Application endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.application import Application
from app.models.match import Match
from app.models.audit import AuditLog
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationListResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/projects/{project_id}/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_project(
    project_id: str,
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply to a project
    
    Args:
        project_id: Project ID
        application_data: Application data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created application
    """
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


@router.get("/me/applications", response_model=ApplicationListResponse)
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's applications
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of applications
    """
    applications = db.query(Application).filter(
        Application.applicant_id == current_user.id
    ).order_by(Application.created_at.desc()).all()
    
    return ApplicationListResponse(
        applications=[ApplicationResponse.from_orm(app) for app in applications]
    )


@router.post("/{application_id}/accept", response_model=SuccessResponse)
async def accept_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an application (project owner only)
    
    Args:
        application_id: Application ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get project
    project = db.query(Project).filter(
        Project.id == application.project_id
    ).first()
    
    # Check if user is project owner
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can accept applications"
        )
    
    # Update application status
    application.status = "accepted"
    application.updated_at = datetime.utcnow()
    
    # Create match
    match = Match(
        project_id=project.id,
        user_a=project.owner_id,
        user_b=application.applicant_id
    )
    db.add(match)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="ACCEPT_APPLICATION",
        resource="applications",
        payload={"application_id": str(application_id)}
    )
    db.add(audit_log)
    
    db.commit()
    
    return SuccessResponse(message="Application accepted")


@router.post("/{application_id}/reject", response_model=SuccessResponse)
async def reject_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject an application (project owner only)
    
    Args:
        application_id: Application ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get project
    project = db.query(Project).filter(
        Project.id == application.project_id
    ).first()
    
    # Check if user is project owner
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can reject applications"
        )
    
    # Update application status
    application.status = "rejected"
    application.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="REJECT_APPLICATION",
        resource="applications",
        payload={"application_id": str(application_id)}
    )
    db.add(audit_log)
    
    db.commit()
    
    return SuccessResponse(message="Application rejected")

