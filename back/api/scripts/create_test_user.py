"""Create a test user for development"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.user import User


def create_test_user():
    """Create a test user"""
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        existing = db.query(User).filter(User.handle == "testuser").first()
        if existing:
            print(f"Test user already exists: {existing.id}")
            return
        
        # Create test user
        user = User(
            handle="testuser",
            email="test@example.com",
            github_login="testuser",
            bio="Test user for development",
            avatar_url="https://avatars.githubusercontent.com/u/1?v=4"
        )
        db.add(user)
        db.flush()
        
        print(f"Created test user: {user.id}")
        print(f"Handle: {user.handle}")
        print(f"Email: {user.email}")
        
        db.commit()
        
    except Exception as e:
        print(f"Error creating test user: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()

