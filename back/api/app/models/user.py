"""User and authentication models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handle = Column(Text, nullable=False, unique=True, index=True)
    email = Column(Text, unique=True, index=True)
    avatar_url = Column(Text)
    bio = Column(Text)
    github_login = Column(Text, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    user_skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    github_repos = relationship("GitHubRepo", back_populates="user", cascade="all, delete-orphan")
    owned_projects = relationship("Project", foreign_keys="Project.owner_id", back_populates="owner")
    applications = relationship("Application", foreign_keys="Application.applicant_id", back_populates="applicant")
    sent_offers = relationship("Offer", foreign_keys="Offer.sender_id", back_populates="sender")
    received_offers = relationship("Offer", foreign_keys="Offer.receiver_id", back_populates="receiver")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    group_messages = relationship("GroupMessage", foreign_keys="GroupMessage.sender_id", back_populates="sender")


class OAuthAccount(Base):
    """OAuth account linkage"""
    __tablename__ = "oauth_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(Text, nullable=False)  # 'github'
    provider_account_id = Column(Text, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id", name="uq_provider_account"),
    )
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")

