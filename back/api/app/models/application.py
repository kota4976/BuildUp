"""Application model for project applications"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Application(Base):
    """User applications to projects"""
    __tablename__ = "applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text)
    status = Column(Text, nullable=False, default="pending")  # pending/accepted/rejected
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("project_id", "applicant_id", name="uq_project_applicant"),
    )
    
    # Relationships
    project = relationship("Project", back_populates="applications")
    applicant = relationship("User", foreign_keys=[applicant_id], back_populates="applications")

