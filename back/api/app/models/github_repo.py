"""GitHub repository model"""
from sqlalchemy import Column, BigInteger, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class GitHubRepo(Base):
    """GitHub repository for user portfolio"""
    __tablename__ = "github_repos"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repo_full_name = Column(Text, nullable=False)  # owner/name
    stars = Column(Integer, nullable=False, default=0)
    language = Column(Text)
    url = Column(Text, nullable=False)
    last_pushed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        UniqueConstraint("user_id", "repo_full_name", name="uq_user_repo"),
    )
    
    # Relationships
    user = relationship("User", back_populates="github_repos")

