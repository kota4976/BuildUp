"""Chat conversation and message models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Conversation(Base):
    """Chat conversation between matched users"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Chat message"""
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_messages_conv_time", "conversation_id", "created_at"),
    )
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")

