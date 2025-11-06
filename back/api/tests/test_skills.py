"""Tests for skill endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_search_skills_empty(client: TestClient):
    """Test searching skills with no query"""
    response = client.get("/api/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data


def test_search_skills_with_query(client: TestClient, test_skill, test_skill2):
    """Test searching skills with query"""
    response = client.get("/api/v1/skills?query=Python")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) > 0
    assert any(s["name"].lower() == "python" for s in data["skills"])


def test_search_skills_with_limit(client: TestClient):
    """Test searching skills with limit"""
    response = client.get("/api/v1/skills?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) <= 5

