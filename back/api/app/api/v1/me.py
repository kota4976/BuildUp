"""Me (current user) endpoints"""
import logging
from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.offer import Offer
from app.models.project import Project

if TYPE_CHECKING:
    from app.schemas.application import ApplicationListResponse
    from app.schemas.offer import OfferListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/applications")
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
    ).options(
        joinedload(Application.project)
    ).order_by(Application.created_at.desc()).all()
    
    from app.schemas.application import ApplicationResponse, ApplicationListResponse
    
    return ApplicationListResponse(
        applications=[ApplicationResponse.from_orm(app) for app in applications]
    )


@router.get("/offers/sent")
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
    # Get projects owned by current user
    owned_project_ids = db.query(Project.id).filter(
        Project.owner_id == current_user.id
    ).subquery()
    
    # Get offers for those projects
    offers = db.query(Offer).filter(
        Offer.project_id.in_(owned_project_ids)
    ).options(
        joinedload(Offer.project),
        joinedload(Offer.receiver)
    ).order_by(Offer.created_at.desc()).all()
    
    from app.schemas.offer import OfferResponse, OfferListResponse
    
    return OfferListResponse(
        offers=[OfferResponse.from_orm(offer) for offer in offers]
    )


@router.get("/offers/received")
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
    ).options(
        joinedload(Offer.project),
        joinedload(Offer.receiver)
    ).order_by(Offer.created_at.desc()).all()
    
    from app.schemas.offer import OfferResponse, OfferListResponse
    
    return OfferListResponse(
        offers=[OfferResponse.from_orm(offer) for offer in offers]
    )

