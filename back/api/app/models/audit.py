"""Audit log model"""
from datetime import datetime
from sqlalchemy import Column, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class AuditLog(Base):
    """Audit log for important actions"""
    __tablename__ = "audit_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(Text, nullable=False)  # e.g. 'LOGIN', 'CREATE_PROJECT'
    resource = Column(Text)
    payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

