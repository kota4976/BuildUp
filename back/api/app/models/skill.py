"""Skill and user skill models"""
from sqlalchemy import Column, Integer, Text, SmallInteger, ForeignKey, CheckConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Skill(Base):
    """Skill master table"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")
    project_skills = relationship("ProjectSkill", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    """User skills with proficiency level"""
    __tablename__ = "user_skills"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    level = Column(SmallInteger, CheckConstraint("level BETWEEN 1 AND 5"))
    
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "skill_id"),
    )
    
    # Relationships
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

