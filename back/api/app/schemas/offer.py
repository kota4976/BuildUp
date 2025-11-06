"""Offer schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, UUID4


class OfferCreate(BaseModel):
    """Offer creation schema"""
    receiver_id: UUID4
    message: Optional[str] = None


class OfferResponse(BaseModel):
    """Offer response schema"""
    id: UUID4
    project_id: UUID4
    sender_id: UUID4
    receiver_id: UUID4
    message: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OfferListResponse(BaseModel):
    """Offer list response"""
    offers: list[OfferResponse]

