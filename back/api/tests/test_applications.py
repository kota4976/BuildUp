"""Tests for application endpoints"""
from fastapi.testclient import TestClient


def test_create_application(
    client: TestClient,
    test_project,
    test_user2,
    auth_headers: dict
):
    """Test creating an application"""
    # Create token for different user (applicant)
    from app.core.security import create_access_token
    applicant_token = create_access_token(data={"sub": str(test_user2.id)})
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    
    application_data = {
        "message": "I'm interested in this project!"
    }
    response = client.post(
        f"/api/v1/projects/{test_project.id}/applications",
        json=application_data,
        headers=applicant_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    assert data["applicant_id"] == str(test_user2.id)
    assert data["status"] == "pending"


def test_create_application_own_project(
    client: TestClient,
    test_project,
    auth_headers: dict
):
    """Test creating application to own project (should fail)"""
    application_data = {"message": "Test"}
    response = client.post(
        f"/api/v1/projects/{test_project.id}/applications",
        json=application_data,
        headers=auth_headers
    )
    assert response.status_code == 400  # Cannot apply to own project


def test_get_my_applications(
    client: TestClient,
    test_project,
    test_user2,
    auth_headers: dict
):
    """Test getting current user's applications"""
    # Create application first
    from app.core.security import create_access_token
    applicant_token = create_access_token(data={"sub": str(test_user2.id)})
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    
    application_data = {"message": "Test application"}
    client.post(
        f"/api/v1/projects/{test_project.id}/applications",
        json=application_data,
        headers=applicant_headers
    )
    
    # Get applications
    response = client.get("/api/v1/me/applications", headers=applicant_headers)
    assert response.status_code == 200
    data = response.json()
    assert "applications" in data
    assert len(data["applications"]) > 0


def test_accept_application(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test accepting an application"""
    # Create application
    from app.core.security import create_access_token
    from app.models.application import Application
    
    applicant_token = create_access_token(data={"sub": str(test_user2.id)})
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    
    application_data = {"message": "Test"}
    create_response = client.post(
        f"/api/v1/projects/{test_project.id}/applications",
        json=application_data,
        headers=applicant_headers
    )
    application_id = create_response.json()["id"]
    
    # Accept application (as project owner)
    response = client.post(
        f"/api/v1/applications/{application_id}/accept",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_reject_application(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test rejecting an application"""
    # Create application
    from app.core.security import create_access_token
    
    applicant_token = create_access_token(data={"sub": str(test_user2.id)})
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    
    application_data = {"message": "Test"}
    create_response = client.post(
        f"/api/v1/projects/{test_project.id}/applications",
        json=application_data,
        headers=applicant_headers
    )
    application_id = create_response.json()["id"]
    
    # Reject application
    response = client.post(
        f"/api/v1/applications/{application_id}/reject",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

