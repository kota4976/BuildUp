"""WebSocket endpoints for chat"""
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.models.match import Match
from app.models.chat import Conversation, Message
from app.services.chat_service import manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_current_user_ws(
    token: str = Query(..., description="JWT token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from WebSocket query parameter
    
    Args:
        token: JWT token from query
        db: Database session
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user from database
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str = Query(...),
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat
    
    Args:
        websocket: WebSocket connection
        conversation_id: Conversation ID
        token: JWT token for authentication
        db: Database session
    """
    try:
        # Authenticate user
        current_user = await get_current_user_ws(token=token, db=db)
        
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Conversation not found")
            return
        
        # Get match to verify user access
        match = db.query(Match).filter(
            Match.id == conversation.match_id
        ).first()
        
        if not match:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Match not found")
            return
        
        # Verify user is part of match
        if match.user_a != current_user.id and match.user_b != current_user.id:
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Not authorized")
            return
        
        # Connect WebSocket
        await manager.connect(websocket, str(current_user.id), str(conversation_id))
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                message_type = data.get("type")
                
                if message_type == "message":
                    # Create message in database
                    message_body = data.get("body", "").strip()
                    
                    if not message_body:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Message body cannot be empty"
                        })
                        continue
                    
                    message = Message(
                        conversation_id=conversation_id,
                        sender_id=current_user.id,
                        body=message_body
                    )
                    db.add(message)
                    db.commit()
                    db.refresh(message)
                    
                    # Broadcast message to all connections in conversation
                    await manager.send_to_conversation(
                        str(conversation_id),
                        {
                            "type": "message",
                            "id": message.id,
                            "sender_id": str(message.sender_id),
                            "body": message.body,
                            "created_at": message.created_at.isoformat()
                        }
                    )
                    
                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
        
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info(f"User {current_user.id} disconnected from conversation {conversation_id}")
        
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            manager.disconnect(websocket)
            try:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except Exception:
                pass
    
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            # Ignore exceptions when closing the WebSocket, as it may already be closed or closing may fail for other reasons.
            pass

