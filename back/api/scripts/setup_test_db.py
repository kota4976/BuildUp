"""Setup test database for running tests"""
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))


def setup_test_database():
    """Create test database if it doesn't exist"""
    try:
        # Try to create database
        result = subprocess.run(
            ["createdb", "buildup_test"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Test database 'buildup_test' created successfully")
        elif "already exists" in result.stderr:
            print("✓ Test database 'buildup_test' already exists")
        else:
            print(f"⚠ Warning: {result.stderr}")
            print("You may need to create the database manually:")
            print("  createdb buildup_test")
    except FileNotFoundError:
        print("⚠ 'createdb' command not found.")
        print("Please make sure PostgreSQL is installed and PATH is configured.")
        print("You can create the database manually:")
        print("  createdb buildup_test")
        print("\nOr use the full path:")
        print("  /opt/homebrew/opt/postgresql@15/bin/createdb buildup_test")


if __name__ == "__main__":
    setup_test_database()

