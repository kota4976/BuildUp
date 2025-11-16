"""Application endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_ # and_ を追加
from datetime import datetime

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.application import Application
from app.models.match import Match
from app.models.audit import AuditLog
from app.schemas.application import (
    ApplicationResponse,
    ApplicationListResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=ApplicationListResponse)
async def get_my_applications(
        type: str = Query(..., description="Filter type: 'received' or 'submitted'"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get applications related to the current user (received by their projects or submitted by them).

    Args:
        type: 'received' (as project owner) or 'submitted' (as applicant)

    Returns:
        List of applications
    """

    # 応募者とプロジェクトオーナーの情報を eager load するための基本クエリ
    q = db.query(Application).options(
        joinedload(Application.applicant),
        joinedload(Application.project).joinedload(Project.owner) # プロジェクトオーナー情報も取得
    )

    if type == "received":
        # 応募されたプロジェクト (current_user がプロジェクトオーナー)
        q = q.join(Project).filter(Project.owner_id == current_user.id)
    elif type == "submitted":
        # 応募したプロジェクト (current_user が応募者)
        q = q.filter(Application.applicant_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type parameter. Must be 'received' or 'submitted'."
        )

    applications = q.order_by(Application.created_at.desc()).all()

    # スキーマに変換して返す
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

