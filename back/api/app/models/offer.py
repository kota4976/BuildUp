"""Offer model for project offers"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Offer(Base):
    """Project owner offers to users"""
    __tablename__ = "offers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text)
    status = Column(Text, nullable=False, default="pending")  # pending/accepted/rejected
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("project_id", "sender_id", "receiver_id", name="uq_project_sender_receiver"),
    )
    
    # Relationships
    project = relationship("Project", back_populates="offers")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_offers")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_offers")

