"""Tests for offer endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_create_offer(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test creating an offer"""
    offer_data = {
        "receiver_id": str(test_user2.id),
        "message": "We'd love to have you on our project!"
    }
    response = client.post(
        f"/api/v1/projects/{test_project.id}/offers",
        json=offer_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    assert data["sender_id"] == str(test_user.id)
    assert data["receiver_id"] == str(test_user2.id)
    assert data["status"] == "pending"


def test_create_offer_unauthorized(
    client: TestClient,
    test_project,
    test_user2,
    auth_headers: dict
):
    """Test creating offer as non-owner (should fail)"""
    # Create token for non-owner
    from app.core.security import create_access_token
    non_owner_token = create_access_token(data={"sub": str(test_user2.id)})
    non_owner_headers = {"Authorization": f"Bearer {non_owner_token}"}
    
    offer_data = {
        "receiver_id": str(test_user2.id),
        "message": "Test"
    }
    response = client.post(
        f"/api/v1/projects/{test_project.id}/offers",
        json=offer_data,
        headers=non_owner_headers
    )
    assert response.status_code == 403  # Only owner can send offers


def test_get_sent_offers(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test getting sent offers"""
    # Create an offer first
    offer_data = {
        "receiver_id": str(test_user2.id),
        "message": "Test offer"
    }
    client.post(
        f"/api/v1/projects/{test_project.id}/offers",
        json=offer_data,
        headers=auth_headers
    )
    
    # Get sent offers
    response = client.get("/api/v1/me/offers/sent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "offers" in data
    assert len(data["offers"]) > 0


def test_get_received_offers(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test getting received offers"""
    # Create an offer first
    offer_data = {
        "receiver_id": str(test_user2.id),
        "message": "Test offer"
    }
    client.post(
        f"/api/v1/projects/{test_project.id}/offers",
        json=offer_data,
        headers=auth_headers
    )
    
    # Get received offers (as receiver)
    from app.core.security import create_access_token
    receiver_token = create_access_token(data={"sub": str(test_user2.id)})
    receiver_headers = {"Authorization": f"Bearer {receiver_token}"}
    
    response = client.get("/api/v1/me/offers/received", headers=receiver_headers)
    assert response.status_code == 200
    data = response.json()
    assert "offers" in data
    assert len(data["offers"]) > 0


def test_accept_offer(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test accepting an offer"""
    # Create an offer
    offer_data = {
        "receiver_id": str(test_user2.id),
        "message": "Test offer"
    }
    create_response = client.post(
        f"/api/v1/projects/{test_project.id}/offers",
        json=offer_data,
        headers=auth_headers
    )
    offer_id = create_response.json()["id"]
    
    # Accept offer (as receiver)
    from app.core.security import create_access_token
    receiver_token = create_access_token(data={"sub": str(test_user2.id)})
    receiver_headers = {"Authorization": f"Bearer {receiver_token}"}
    
    response = client.post(
        f"/api/v1/offers/{offer_id}/accept",
        headers=receiver_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_reject_offer(
    client: TestClient,
    test_project,
    test_user,
    test_user2,
    auth_headers: dict
):
    """Test rejecting an offer"""
    # Create an offer
    offer_data = {
        "receiver_id": str(test_user2.id),
        "message": "Test offer"
    }
    create_response = client.post(
        f"/api/v1/projects/{test_project.id}/offers",
        json=offer_data,
        headers=auth_headers
    )
    offer_id = create_response.json()["id"]
    
    # Reject offer
    from app.core.security import create_access_token
    receiver_token = create_access_token(data={"sub": str(test_user2.id)})
    receiver_headers = {"Authorization": f"Bearer {receiver_token}"}
    
    response = client.post(
        f"/api/v1/offers/{offer_id}/reject",
        headers=receiver_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

