"""Project and related models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey, Integer, SmallInteger, CheckConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    """Project recruitment"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="open")  # open/closed
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    project_skills = relationship("ProjectSkill", back_populates="project", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="project", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="project", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="project", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="project", cascade="all, delete-orphan")


class ProjectSkill(Base):
    """Required skills for project"""
    __tablename__ = "project_skills"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    required_level = Column(SmallInteger, CheckConstraint("required_level BETWEEN 1 AND 5"))
    
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "skill_id"),
    )
    
    # Relationships
    project = relationship("Project", back_populates="project_skills")
    skill = relationship("Skill", back_populates="project_skills")


class Favorite(Base):
    """User favorites for projects"""
    __tablename__ = "favorites"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "project_id"),
    )
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    project = relationship("Project", back_populates="favorites")

