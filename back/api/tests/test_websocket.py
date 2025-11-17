"""End-to-end tests for WebSocket chat endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.chat import Conversation, Message
from app.models.match import Match
from app.models.group_chat import GroupConversation, GroupMember, MemberRole


@pytest.fixture
def conversation_with_match(
    db_session: Session,
    test_project,
    test_user,
    test_user2
) -> Conversation:
    """Create a 1-on-1 conversation and match."""
    match = Match(
        project_id=test_project.id,
        user_a=test_user.id,
        user_b=test_user2.id
    )
    db_session.add(match)
    db_session.flush()

    conversation = Conversation(match_id=match.id)
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


@pytest.fixture
def group_conversation_with_members(
    db_session: Session,
    test_project,
    test_user,
    test_user2
) -> GroupConversation:
    """Create a group conversation with two members."""
    group_conv = GroupConversation(
        project_id=test_project.id,
        name="WebRTC Study Group"
    )
    db_session.add(group_conv)
    db_session.flush()

    owner_member = GroupMember(
        group_conversation_id=group_conv.id,
        user_id=test_user.id,
        role=MemberRole.owner
    )
    regular_member = GroupMember(
        group_conversation_id=group_conv.id,
        user_id=test_user2.id,
        role=MemberRole.member
    )
    db_session.add_all([owner_member, regular_member])
    db_session.commit()
    db_session.refresh(group_conv)
    return group_conv


def test_chat_websocket_message_and_signaling(
    client: TestClient,
    db_session: Session,
    conversation_with_match: Conversation,
    test_user,
    test_user2
):
    """Validate 1-on-1 chat message storage and WebRTC signaling forwarding."""
    conversation_id = str(conversation_with_match.id)
    token_owner = create_access_token(data={"sub": str(test_user.id)})
    token_member = create_access_token(data={"sub": str(test_user2.id)})

    url_owner = f"/ws/chat?conversation_id={conversation_id}&token={token_owner}"
    url_member = f"/ws/chat?conversation_id={conversation_id}&token={token_member}"

    with client.websocket_connect(url_owner) as ws_owner, client.websocket_connect(url_member) as ws_member:
        # Send a plain chat message
        ws_owner.send_json({"type": "message", "body": "Hello via WebSocket!"})
        delivered_message = ws_member.receive_json()

        assert delivered_message["type"] == "message"
        assert delivered_message["body"] == "Hello via WebSocket!"
        assert delivered_message["sender_id"] == str(test_user.id)

        # Ensure the message is persisted
        stored_messages = db_session.query(Message).all()
        assert len(stored_messages) == 1
        assert stored_messages[0].body == "Hello via WebSocket!"
        assert stored_messages[0].sender_id == test_user.id
        assert str(stored_messages[0].conversation_id) == conversation_id

        # Send WebRTC offer signaling data and ensure it is forwarded
        signaling_payload = {
            "type": "offer",
            "target_user_id": str(test_user2.id),
            "sdp": "dummy-sdp",
            "is_video": False
        }
        ws_owner.send_json(signaling_payload)
        forwarded_signal = ws_member.receive_json()

        assert forwarded_signal["type"] == "offer"
        assert forwarded_signal["sdp"] == "dummy-sdp"
        assert forwarded_signal["sender_id"] == str(test_user.id)
        assert forwarded_signal["sender_name"] == test_user.handle
        assert forwarded_signal["conversation_id"] == conversation_id
        assert forwarded_signal["is_video"] is False


def test_group_chat_websocket_signaling_flow(
    client: TestClient,
    group_conversation_with_members: GroupConversation,
    test_user,
    test_user2
):
    """Validate group chat broadcasting and WebRTC signaling forwarding."""
    group_id = str(group_conversation_with_members.id)
    token_owner = create_access_token(data={"sub": str(test_user.id)})
    token_member = create_access_token(data={"sub": str(test_user2.id)})

    url_owner = f"/ws/group-chat?group_conversation_id={group_id}&token={token_owner}"
    url_member = f"/ws/group-chat?group_conversation_id={group_id}&token={token_member}"

    with client.websocket_connect(url_owner) as ws_owner, client.websocket_connect(url_member) as ws_member:
        # Broadcast a group chat message
        ws_owner.send_json({"type": "message", "body": "Hello group!"})
        delivered_message = ws_member.receive_json()

        assert delivered_message["type"] == "message"
        assert delivered_message["body"] == "Hello group!"
        assert delivered_message["sender_id"] == str(test_user.id)

        # Send an ICE candidate signaling payload
        ice_payload = {
            "type": "ice-candidate",
            "target_user_id": str(test_user2.id),
            "candidate": {
                "candidate": "candidate:1 1 UDP 2122260223 192.0.2.1 3478 typ host",
                "sdpMLineIndex": 0
            }
        }
        ws_owner.send_json(ice_payload)
        forwarded_signal = ws_member.receive_json()

        assert forwarded_signal["type"] == "ice-candidate"
        assert forwarded_signal["candidate"]["candidate"].startswith("candidate:")
        assert forwarded_signal["sender_id"] == str(test_user.id)
        assert forwarded_signal["sender_name"] == test_user.handle
        assert forwarded_signal["conversation_id"] == group_id

