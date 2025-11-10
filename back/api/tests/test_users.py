"""Tests for user endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_get_user(client: TestClient, test_user, auth_headers: dict):
    """Test getting user by ID"""
    response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["handle"] == "testuser"
    assert "skills" in data
    assert "repos" in data


def test_get_user_not_found(client: TestClient, auth_headers: dict):
    """Test getting non-existent user"""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/users/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_update_current_user(client: TestClient, test_user, auth_headers: dict):
    """Test updating current user profile"""
    update_data = {
        "bio": "Updated bio",
        "avatar_url": "https://example.com/new-avatar.jpg"
    }
    response = client.patch(
        "/api/v1/users/me",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "Updated bio"
    assert data["avatar_url"] == "https://example.com/new-avatar.jpg"


def test_update_user_skills(
    client: TestClient,
    test_user,
    test_skill,
    test_skill2,
    auth_headers: dict
):
    """Test updating user skills"""
    skills_data = [
        {"skill_id": test_skill.id, "level": 5},
        {"skill_id": test_skill2.id, "level": 3}
    ]
    response = client.put(
        "/api/v1/users/me/skills",
        json=skills_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify skills were updated
    user_response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert len(user_data["skills"]) == 2
    skill_ids = [s["skill_id"] for s in user_data["skills"]]
    assert test_skill.id in skill_ids
    assert test_skill2.id in skill_ids


def test_update_user_skills_invalid_level(client: TestClient, test_skill, auth_headers: dict):
    """Test updating user skills with invalid level"""
    skills_data = [
        {"skill_id": test_skill.id, "level": 10}  # Invalid level (> 5)
    ]
    response = client.put(
        "/api/v1/users/me/skills",
        json=skills_data,
        headers=auth_headers
    )
    assert response.status_code == 400


def test_update_user_skills_nonexistent_skill(client: TestClient, auth_headers: dict):
    """Test updating user skills with non-existent skill"""
    skills_data = [
        {"skill_id": 99999, "level": 3}  # Non-existent skill
    ]
    response = client.put(
        "/api/v1/users/me/skills",
        json=skills_data,
        headers=auth_headers
    )
    assert response.status_code == 404

