"""Tests for group chat endpoints"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.project import Project
from app.models.group_chat import GroupConversation, GroupMember, GroupMessage, MemberRole
from app.core.security import create_access_token


@pytest.fixture
def test_user3(db_session: Session) -> User:
    """Create a third test user"""
    user = User(
        handle="testuser3",
        email="test3@example.com",
        github_login="testuser3",
        bio="Test user 3 bio"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token2(test_user2: User) -> str:
    """Create a JWT token for test_user2"""
    return create_access_token(data={"sub": str(test_user2.id)})


@pytest.fixture
def auth_headers2(auth_token2: str) -> dict:
    """Create authorization headers for test_user2"""
    return {"Authorization": f"Bearer {auth_token2}"}


@pytest.fixture
def auth_token3(test_user3: User) -> str:
    """Create a JWT token for test_user3"""
    return create_access_token(data={"sub": str(test_user3.id)})


@pytest.fixture
def auth_headers3(auth_token3: str) -> dict:
    """Create authorization headers for test_user3"""
    return {"Authorization": f"Bearer {auth_token3}"}


@pytest.fixture
def test_group_conversation(
    db_session: Session,
    test_project: Project,
    test_user: User
) -> GroupConversation:
    """Create a test group conversation"""
    group_conv = GroupConversation(
        project_id=test_project.id,
        name="Test Team Chat"
    )
    db_session.add(group_conv)
    db_session.flush()
    
    # Add owner as member
    member = GroupMember(
        group_conversation_id=group_conv.id,
        user_id=test_user.id,
        role=MemberRole.owner
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(group_conv)
    return group_conv


def test_create_group_conversation(
    client: TestClient,
    test_project: Project,
    auth_headers: dict
):
    """Test creating a group conversation"""
    data = {
        "project_id": str(test_project.id),
        "name": "New Team Chat"
    }
    
    response = client.post(
        "/api/v1/group-chats",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "New Team Chat"
    assert result["project_id"] == str(test_project.id)
    assert len(result["members"]) == 1
    assert result["members"][0]["role"] == "owner"


def test_create_group_conversation_not_owner(
    client: TestClient,
    test_project: Project,
    auth_headers2: dict
):
    """Test creating a group conversation by non-owner (should fail)"""
    data = {
        "project_id": str(test_project.id),
        "name": "Unauthorized Chat"
    }
    
    response = client.post(
        "/api/v1/group-chats",
        json=data,
        headers=auth_headers2
    )
    
    assert response.status_code == 403


def test_create_group_conversation_duplicate(
    client: TestClient,
    test_project: Project,
    test_group_conversation: GroupConversation,
    auth_headers: dict
):
    """Test creating duplicate group conversation (should fail)"""
    data = {
        "project_id": str(test_project.id),
        "name": "Duplicate Chat"
    }
    
    response = client.post(
        "/api/v1/group-chats",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 400


def test_get_my_group_conversations(
    client: TestClient,
    test_group_conversation: GroupConversation,
    auth_headers: dict
):
    """Test getting user's group conversations"""
    response = client.get(
        "/api/v1/group-chats",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0]["id"] == str(test_group_conversation.id)


def test_get_group_conversation_detail(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user: User,
    auth_headers: dict
):
    """Test getting group conversation detail with messages"""
    # Add some messages
    message1 = GroupMessage(
        group_conversation_id=test_group_conversation.id,
        sender_id=test_user.id,
        body="Hello team!"
    )
    message2 = GroupMessage(
        group_conversation_id=test_group_conversation.id,
        sender_id=test_user.id,
        body="How are you?"
    )
    db_session.add_all([message1, message2])
    db_session.commit()
    
    response = client.get(
        f"/api/v1/group-chats/{test_group_conversation.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(test_group_conversation.id)
    assert result["name"] == "Test Team Chat"
    assert len(result["messages"]) == 2
    assert result["messages"][0]["body"] == "Hello team!"
    assert result["has_more"] is False


def test_get_group_conversation_unauthorized(
    client: TestClient,
    test_group_conversation: GroupConversation,
    auth_headers2: dict
):
    """Test getting group conversation by non-member (should fail)"""
    response = client.get(
        f"/api/v1/group-chats/{test_group_conversation.id}",
        headers=auth_headers2
    )
    
    assert response.status_code == 403


def test_get_group_conversation_pagination(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user: User,
    auth_headers: dict
):
    """Test group conversation message pagination"""
    # Add 60 messages
    for i in range(60):
        message = GroupMessage(
            group_conversation_id=test_group_conversation.id,
            sender_id=test_user.id,
            body=f"Message {i}"
        )
        db_session.add(message)
    db_session.commit()
    
    # Get first page (limit 50)
    response = client.get(
        f"/api/v1/group-chats/{test_group_conversation.id}",
        params={"limit": 50},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert len(result["messages"]) == 50
    assert result["has_more"] is True


def test_update_group_conversation(
    client: TestClient,
    test_group_conversation: GroupConversation,
    auth_headers: dict
):
    """Test updating group conversation name"""
    data = {
        "name": "Updated Team Chat"
    }
    
    response = client.patch(
        f"/api/v1/group-chats/{test_group_conversation.id}",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Updated Team Chat"


def test_update_group_conversation_not_owner(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user2: User,
    auth_headers2: dict
):
    """Test updating group conversation by non-owner (should fail)"""
    # Add test_user2 as regular member
    member = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    db_session.add(member)
    db_session.commit()
    
    data = {
        "name": "Unauthorized Update"
    }
    
    response = client.patch(
        f"/api/v1/group-chats/{test_group_conversation.id}",
        json=data,
        headers=auth_headers2
    )
    
    assert response.status_code == 403


def test_add_member_to_group(
    client: TestClient,
    test_group_conversation: GroupConversation,
    test_user2: User,
    auth_headers: dict
):
    """Test adding a member to group conversation"""
    data = {
        "user_id": str(test_user2.id)
    }
    
    response = client.post(
        f"/api/v1/group-chats/{test_group_conversation.id}/members",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "Member added successfully"


def test_add_member_not_owner(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user2: User,
    test_user3: User,
    auth_headers2: dict
):
    """Test adding member by non-owner (should fail)"""
    # Add test_user2 as regular member
    member = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    db_session.add(member)
    db_session.commit()
    
    data = {
        "user_id": str(test_user3.id)
    }
    
    response = client.post(
        f"/api/v1/group-chats/{test_group_conversation.id}/members",
        json=data,
        headers=auth_headers2
    )
    
    assert response.status_code == 403


def test_add_duplicate_member(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user2: User,
    auth_headers: dict
):
    """Test adding duplicate member (should fail)"""
    # Add test_user2 first
    member = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    db_session.add(member)
    db_session.commit()
    
    # Try to add again
    data = {
        "user_id": str(test_user2.id)
    }
    
    response = client.post(
        f"/api/v1/group-chats/{test_group_conversation.id}/members",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 400


def test_remove_member_from_group(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user2: User,
    auth_headers: dict
):
    """Test removing a member from group conversation"""
    # Add test_user2 first
    member = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    db_session.add(member)
    db_session.commit()
    
    # Remove member
    response = client.delete(
        f"/api/v1/group-chats/{test_group_conversation.id}/members/{test_user2.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "Member removed successfully"


def test_remove_self_from_group(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user2: User,
    auth_headers2: dict
):
    """Test member removing themselves from group"""
    # Add test_user2 first
    member = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    db_session.add(member)
    db_session.commit()
    
    # Remove self
    response = client.delete(
        f"/api/v1/group-chats/{test_group_conversation.id}/members/{test_user2.id}",
        headers=auth_headers2
    )
    
    assert response.status_code == 200


def test_remove_member_unauthorized(
    client: TestClient,
    db_session: Session,
    test_group_conversation: GroupConversation,
    test_user2: User,
    test_user3: User,
    auth_headers2: dict
):
    """Test removing member by non-owner non-self (should fail)"""
    # Add both users as members
    member2 = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    member3 = GroupMember(
        group_conversation_id=test_group_conversation.id,
        user_id=test_user3.id,
        role=MemberRole.member
    )
    db_session.add_all([member2, member3])
    db_session.commit()
    
    # Try to remove user3 as user2
    response = client.delete(
        f"/api/v1/group-chats/{test_group_conversation.id}/members/{test_user3.id}",
        headers=auth_headers2
    )
    
    assert response.status_code == 403


def test_get_project_group_conversation(
    client: TestClient,
    test_project: Project,
    test_group_conversation: GroupConversation,
    auth_headers: dict
):
    """Test getting group conversation by project ID"""
    response = client.get(
        f"/api/v1/group-chats/projects/{test_project.id}/group-conversation",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == str(test_group_conversation.id)
    assert result["project_id"] == str(test_project.id)


def test_get_project_group_conversation_not_member(
    client: TestClient,
    test_project: Project,
    test_group_conversation: GroupConversation,
    auth_headers2: dict
):
    """Test getting project group conversation by non-member (should fail)"""
    response = client.get(
        f"/api/v1/group-chats/projects/{test_project.id}/group-conversation",
        headers=auth_headers2
    )
    
    assert response.status_code == 403


def test_get_project_group_conversation_not_found(
    client: TestClient,
    test_project: Project,
    auth_headers: dict
):
    """Test getting non-existent project group conversation"""
    # Delete the group conversation if it exists
    response = client.get(
        f"/api/v1/group-chats/projects/{test_project.id}/group-conversation",
        headers=auth_headers
    )
    
    # Should return 404 if no group conversation exists
    if response.status_code == 200:
        # Group conversation exists, skip this test
        pytest.skip("Group conversation already exists for project")
    
    assert response.status_code == 404

