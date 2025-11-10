"""Match and conversation models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Match(Base):
    """Successful matches between users and projects"""
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_a = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_b = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("project_id", "user_a", "user_b", name="uq_project_users"),
    )
    
    # Relationships
    project = relationship("Project", back_populates="matches")
    conversations = relationship("Conversation", back_populates="match", cascade="all, delete-orphan")

