"""Offer endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.offer import Offer
from app.models.match import Match
from app.models.audit import AuditLog
from app.schemas.offer import (
    OfferCreate,
    OfferResponse,
    OfferListResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/projects/{project_id}/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    project_id: str,
    offer_data: OfferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an offer to a user for a project
    
    Args:
        project_id: Project ID
        offer_data: Offer data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created offer
    """
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


@router.get("/me/offers/sent", response_model=OfferListResponse)
async def get_sent_offers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get offers sent by current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of sent offers
    """
    offers = db.query(Offer).filter(
        Offer.sender_id == current_user.id
    ).order_by(Offer.created_at.desc()).all()
    
    return OfferListResponse(
        offers=[OfferResponse.from_orm(offer) for offer in offers]
    )


@router.get("/me/offers/received", response_model=OfferListResponse)
async def get_received_offers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get offers received by current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of received offers
    """
    offers = db.query(Offer).filter(
        Offer.receiver_id == current_user.id
    ).order_by(Offer.created_at.desc()).all()
    
    return OfferListResponse(
        offers=[OfferResponse.from_orm(offer) for offer in offers]
    )


@router.post("/{offer_id}/accept", response_model=SuccessResponse)
async def accept_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an offer (receiver only)
    
    Args:
        offer_id: Offer ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    offer = db.query(Offer).filter(
        Offer.id == offer_id
    ).first()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    # Check if user is receiver
    if offer.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only offer receiver can accept"
        )
    
    # Update offer status
    offer.status = "accepted"
    offer.updated_at = datetime.utcnow()
    
    # Create match
    match = Match(
        project_id=offer.project_id,
        user_a=offer.sender_id,
        user_b=offer.receiver_id
    )
    db.add(match)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="ACCEPT_OFFER",
        resource="offers",
        payload={"offer_id": str(offer_id)}
    )
    db.add(audit_log)
    
    db.commit()
    
    return SuccessResponse(message="Offer accepted")


@router.post("/{offer_id}/reject", response_model=SuccessResponse)
async def reject_offer(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject an offer (receiver only)
    
    Args:
        offer_id: Offer ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    offer = db.query(Offer).filter(
        Offer.id == offer_id
    ).first()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    # Check if user is receiver
    if offer.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only offer receiver can reject"
        )
    
    # Update offer status
    offer.status = "rejected"
    offer.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="REJECT_OFFER",
        resource="offers",
        payload={"offer_id": str(offer_id)}
    )
    db.add(audit_log)
    
    db.commit()
    
    return SuccessResponse(message="Offer rejected")

