"""Pytest configuration and fixtures"""
import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Set test database URL before importing app
os.environ["DATABASE_URL"] = "postgresql://localhost:5432/buildup_test"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["GITHUB_CLIENT_ID"] = "test_client_id"
os.environ["GITHUB_CLIENT_SECRET"] = "test_client_secret"
os.environ["GITHUB_REDIRECT_URI"] = "http://localhost/api/v1/auth/github/callback"
os.environ["APP_ENV"] = "test"

from app.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.skill import Skill
from app.models.project import Project
from main import app


# Create test database engine
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/buildup_test")
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    
    # Enable PostgreSQL extensions
    try:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        session.commit()
    except Exception:
        # If extension already exists or cannot be created, continue
        session.rollback()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user"""
    user = User(
        handle="testuser",
        email="test@example.com",
        github_login="testuser",
        bio="Test user bio",
        avatar_url="https://example.com/avatar.jpg"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session: Session) -> User:
    """Create a second test user"""
    user = User(
        handle="testuser2",
        email="test2@example.com",
        github_login="testuser2",
        bio="Test user 2 bio"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_skill(db_session: Session) -> Skill:
    """Create a test skill"""
    skill = Skill(name="Python")
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


@pytest.fixture
def test_skill2(db_session: Session) -> Skill:
    """Create a second test skill"""
    skill = Skill(name="JavaScript")
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


@pytest.fixture
def test_project(db_session: Session, test_user: User, test_skill: Skill) -> Project:
    """Create a test project"""
    from app.models.project import ProjectSkill
    
    project = Project(
        owner_id=test_user.id,
        title="Test Project",
        description="Test project description",
        status="open"
    )
    db_session.add(project)
    db_session.flush()
    
    project_skill = ProjectSkill(
        project_id=project.id,
        skill_id=test_skill.id,
        required_level=3
    )
    db_session.add(project_skill)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create a JWT token for test user"""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}

