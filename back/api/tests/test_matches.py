"""Tests for match endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_get_my_matches(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test getting user's matches"""
    # Create a match first
    from app.models.match import Match
    from app.models.application import Application
    
    # Create and accept an application to create a match
    from app.core.security import create_access_token
    applicant_token = create_access_token(data={"sub": str(test_user2.id)})
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    
    # Create application
    application_data = {"message": "Test"}
    create_response = client.post(
        f"/api/v1/projects/{test_project.id}/applications",
        json=application_data,
        headers=applicant_headers
    )
    application_id = create_response.json()["id"]
    
    # Accept application to create match
    client.post(
        f"/api/v1/applications/{application_id}/accept",
        headers=auth_headers
    )
    
    # Get matches
    response = client.get("/api/v1/matches/me/matches", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) > 0


def test_get_conversation(
    client: TestClient,
    db_session,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test getting conversation for a match"""
    # Create a match and conversation
    from app.models.match import Match
    from app.models.chat import Conversation
    
    # Create match
    match = Match(
        project_id=test_project.id,
        user_a=test_user.id,
        user_b=test_user2.id
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    
    # Create conversation
    conversation = Conversation(match_id=match.id)
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    
    # Get conversation
    response = client.get(
        f"/api/v1/matches/{match.id}/conversation",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "match_id" in data
    assert "messages" in data
    assert data["match_id"] == str(match.id)

