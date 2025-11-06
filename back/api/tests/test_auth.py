"""Tests for authentication endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_github_login_redirect(client: TestClient):
    """Test GitHub OAuth login redirect"""
    response = client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert "github.com" in response.headers.get("location", "")


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without authentication"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # Forbidden when no token


def test_get_current_user_authorized(client: TestClient, auth_headers: dict):
    """Test getting current user with authentication"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "handle" in data
    assert data["handle"] == "testuser"


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401  # Unauthorized

