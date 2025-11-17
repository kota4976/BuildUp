"""Tests for authentication endpoints"""
from urllib.parse import urlparse, parse_qsl

from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from app.models.user import OAuthAccount, User
from app.services.github_service import GitHubService


def _assert_profile_redirect(response: Response) -> dict:
    """
    Assert that the GitHub callback now redirects to the profile page with tokens in the fragment.
    Returns the fragment parameters for further inspection.
    """
    assert response.status_code == 307
    location = response.headers.get("location")
    assert location is not None
    assert location.startswith("http://localhost/profile.html#")

    parsed = urlparse(location)
    fragment_params = dict(parse_qsl(parsed.fragment))
    assert fragment_params.get("access_token")
    assert fragment_params.get("token_type") == "bearer"
    return fragment_params


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


def test_github_callback_reuses_existing_user(
    client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch
):
    """GitHub callback should attach OAuth data to an existing user instead of duplicating."""

    async def mock_exchange_code_for_token(code: str):
        assert code == "sample_code"
        return {"access_token": "token123"}

    async def mock_get_user_info(access_token: str):
        assert access_token == "token123"
        return {
            "id": 123456,
            "login": test_user.github_login,
            "avatar_url": "https://avatars.githubusercontent.com/u/123456?v=4",
            "bio": "Updated bio"
        }

    async def mock_get_user_emails(access_token: str):
        assert access_token == "token123"
        return [{"email": test_user.email, "primary": True}]

    monkeypatch.setattr(GitHubService, "exchange_code_for_token", mock_exchange_code_for_token)
    monkeypatch.setattr(GitHubService, "get_user_info", mock_get_user_info)
    monkeypatch.setattr(GitHubService, "get_user_emails", mock_get_user_emails)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "sample_code"},
        follow_redirects=False
    )

    tokens = _assert_profile_redirect(response)
    assert tokens["access_token"]  # non-empty token issued

    oauth_accounts = (
        db_session.query(OAuthAccount)
        .filter(
            OAuthAccount.user_id == test_user.id,
            OAuthAccount.provider == "github",
            OAuthAccount.provider_account_id == "123456"
        )
        .all()
    )
    assert len(oauth_accounts) == 1
    assert oauth_accounts[0].access_token == "token123"


def test_github_callback_generates_unique_handle(client: TestClient, db_session: Session, monkeypatch):
    """New GitHub users should get a unique handle even if the preferred one is taken."""
    # Existing user occupying the base handle
    existing_user = User(
        handle="duplicate",
        email="existing@example.com",
        github_login="existing",
        bio="Existing user"
    )
    db_session.add(existing_user)
    db_session.commit()

    async def mock_exchange_code_for_token(code: str):
        return {"access_token": "token456"}

    async def mock_get_user_info(access_token: str):
        return {
            "id": 654321,
            "login": "duplicate",
            "avatar_url": "https://avatars.githubusercontent.com/u/654321?v=4",
            "bio": "New user bio"
        }

    async def mock_get_user_emails(access_token: str):
        return [{"email": "newuser@example.com", "primary": True}]

    monkeypatch.setattr(GitHubService, "exchange_code_for_token", mock_exchange_code_for_token)
    monkeypatch.setattr(GitHubService, "get_user_info", mock_get_user_info)
    monkeypatch.setattr(GitHubService, "get_user_emails", mock_get_user_emails)

    response = client.get(
        "/api/v1/auth/github/callback",
        params={"code": "another_code"},
        follow_redirects=False
    )

    tokens = _assert_profile_redirect(response)
    assert tokens["access_token"]

    new_user = db_session.query(User).filter(User.github_login == "duplicate").one()
    assert new_user.handle == "duplicate-1"

    oauth_record = (
        db_session.query(OAuthAccount)
        .filter(
            OAuthAccount.provider_account_id == "654321",
            OAuthAccount.provider == "github"
        )
        .one()
    )
    assert oauth_record.user_id == new_user.id

