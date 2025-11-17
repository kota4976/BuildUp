"""Group chat models for project collaboration"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, BigInteger, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class MemberRole(str, enum.Enum):
    """Role of a member in group conversation"""
    owner = "owner"
    member = "member"


class GroupConversation(Base):
    """Group chat conversation for project collaboration or general purpose"""
    __tablename__ = "group_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, unique=True)  # Optional: for project-based groups
    name = Column(Text, nullable=False)  # e.g., "Project ABC Team Chat" or "My Friends"
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="group_conversation")
    members = relationship("GroupMember", back_populates="group_conversation", cascade="all, delete-orphan")
    messages = relationship("GroupMessage", back_populates="group_conversation", cascade="all, delete-orphan")


class GroupMember(Base):
    """Member of a group conversation"""
    __tablename__ = "group_members"
    
    group_conversation_id = Column(UUID(as_uuid=True), ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    role = Column(SQLEnum(MemberRole), nullable=False, default=MemberRole.member)
    joined_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    group_conversation = relationship("GroupConversation", back_populates="members")
    user = relationship("User", back_populates="group_memberships")


class GroupMessage(Base):
    """Message in a group conversation"""
    __tablename__ = "group_messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_conversation_id = Column(UUID(as_uuid=True), ForeignKey("group_conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_group_messages_conv_time", "group_conversation_id", "created_at"),
    )
    
    # Relationships
    group_conversation = relationship("GroupConversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="group_messages")

