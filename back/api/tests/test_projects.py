"""Tests for project endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_create_project(
    client: TestClient,
    test_user,
    test_skill,
    auth_headers: dict
):
    """Test creating a project"""
    project_data = {
        "title": "New Test Project",
        "description": "This is a new test project",
        "required_skills": [
            {"skill_id": test_skill.id, "required_level": 4}
        ]
    }
    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Test Project"
    assert data["description"] == "This is a new test project"
    assert data["status"] == "open"
    assert data["owner_id"] == str(test_user.id)


def test_list_projects(client: TestClient, test_project, auth_headers: dict):
    """Test listing projects"""
    response = client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert len(data["projects"]) > 0


def test_list_projects_with_query(client: TestClient, test_project, auth_headers: dict):
    """Test listing projects with search query"""
    response = client.get(
        "/api/v1/projects?query=Test",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert len(data["projects"]) > 0


def test_list_projects_with_skill_filter(
    client: TestClient,
    test_project,
    test_skill,
    auth_headers: dict
):
    """Test listing projects filtered by skill"""
    response = client.get(
        f"/api/v1/projects?skill_id={test_skill.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data


def test_get_project(client: TestClient, test_project, auth_headers: dict):
    """Test getting project by ID"""
    response = client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_project.id)
    assert data["title"] == "Test Project"
    assert "required_skills" in data


def test_get_project_not_found(client: TestClient, auth_headers: dict):
    """Test getting non-existent project"""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(
        f"/api/v1/projects/{fake_id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_update_project(
    client: TestClient,
    test_project,
    test_user,
    auth_headers: dict
):
    """Test updating project"""
    update_data = {
        "title": "Updated Project Title",
        "description": "Updated description",
        "status": "closed"
    }
    response = client.patch(
        f"/api/v1/projects/{test_project.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Project Title"
    assert data["status"] == "closed"


def test_update_project_unauthorized(
    client: TestClient,
    test_project,
    test_user2,
    auth_headers: dict
):
    """Test updating project as non-owner"""
    # Create token for different user
    from app.core.security import create_access_token
    other_token = create_access_token(data={"sub": str(test_user2.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    update_data = {"title": "Unauthorized Update"}
    response = client.patch(
        f"/api/v1/projects/{test_project.id}",
        json=update_data,
        headers=other_headers
    )
    assert response.status_code == 403


def test_favorite_project(client: TestClient, test_project, auth_headers: dict):
    """Test adding project to favorites"""
    response = client.post(
        f"/api/v1/projects/{test_project.id}/favorite",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_unfavorite_project(client: TestClient, test_project, auth_headers: dict):
    """Test removing project from favorites"""
    # First add to favorites
    client.post(
        f"/api/v1/projects/{test_project.id}/favorite",
        headers=auth_headers
    )
    
    # Then remove
    response = client.delete(
        f"/api/v1/projects/{test_project.id}/favorite",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

