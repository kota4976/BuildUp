"""Match endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.match import Match
from app.models.chat import Conversation, Message
from app.schemas.match import (
    MatchResponse,
    MatchListResponse,
    ConversationResponse,
    MessageResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me/matches", response_model=MatchListResponse)
async def get_my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's matches
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of matches
    """
    matches = db.query(Match).filter(
        or_(
            Match.user_a == current_user.id,
            Match.user_b == current_user.id
        )
    ).order_by(Match.created_at.desc()).all()
    
    return MatchListResponse(
        matches=[MatchResponse.from_orm(match) for match in matches]
    )


@router.get("/{match_id}/conversation", response_model=ConversationResponse)
async def get_conversation(
    match_id: str,
    limit: int = Query(50, ge=1, le=100),
    before_id: int = Query(None, description="Get messages before this ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation for a match
    
    Args:
        match_id: Match ID
        limit: Maximum number of messages
        before_id: Get messages before this message ID (for pagination)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Conversation with messages
    """
    # Get match
    match = db.query(Match).filter(
        Match.id == match_id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Check if user is part of match
    if match.user_a != current_user.id and match.user_b != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this conversation"
        )
    
    # Get or create conversation
    conversation = db.query(Conversation).filter(
        Conversation.match_id == match_id
    ).first()
    
    if not conversation:
        conversation = Conversation(match_id=match_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Get messages
    q = db.query(Message).filter(
        Message.conversation_id == conversation.id
    )
    
    if before_id:
        q = q.filter(Message.id < before_id)
    
    messages = q.order_by(Message.created_at.desc()).limit(limit + 1).all()
    
    # Check if there are more messages
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]
    
    # Reverse to show oldest first
    messages.reverse()
    
    return ConversationResponse(
        id=conversation.id,
        match_id=match_id,
        messages=[MessageResponse.from_orm(msg) for msg in messages],
        has_more=has_more
    )

