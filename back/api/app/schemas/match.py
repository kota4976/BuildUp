"""Match and conversation schemas"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, UUID4


class MatchResponse(BaseModel):
    """Match response schema"""
    id: UUID4
    project_id: UUID4
    user_a: UUID4
    user_b: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Match list response"""
    matches: List[MatchResponse]


class MessageResponse(BaseModel):
    """Message response schema"""
    id: int
    conversation_id: UUID4
    sender_id: UUID4
    body: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response schema"""
    id: UUID4
    match_id: UUID4
    messages: List[MessageResponse]
    has_more: bool = False

