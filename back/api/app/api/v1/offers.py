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
    OfferResponse,
    OfferListResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


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

