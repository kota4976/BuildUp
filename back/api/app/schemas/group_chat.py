"""Group chat schemas"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, UUID4, Field
from app.models.group_chat import MemberRole


class GroupConversationCreate(BaseModel):
    """Schema for creating a group conversation"""
    project_id: UUID4
    name: str = Field(..., min_length=1, max_length=200)


class GroupMemberResponse(BaseModel):
    """Group member response schema"""
    user_id: UUID4
    role: MemberRole
    joined_at: datetime
    
    class Config:
        from_attributes = True


class GroupMessageResponse(BaseModel):
    """Group message response schema"""
    id: int
    group_conversation_id: UUID4
    sender_id: UUID4
    body: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class GroupConversationResponse(BaseModel):
    """Group conversation response schema"""
    id: UUID4
    project_id: UUID4
    name: str
    created_at: datetime
    updated_at: datetime
    members: List[GroupMemberResponse] = []
    
    class Config:
        from_attributes = True


class GroupConversationDetailResponse(BaseModel):
    """Detailed group conversation with messages"""
    id: UUID4
    project_id: UUID4
    name: str
    created_at: datetime
    updated_at: datetime
    members: List[GroupMemberResponse]
    messages: List[GroupMessageResponse]
    has_more: bool = False


class GroupMessageCreate(BaseModel):
    """Schema for creating a group message"""
    body: str = Field(..., min_length=1, max_length=10000)


class GroupMemberAdd(BaseModel):
    """Schema for adding a member to group"""
    user_id: UUID4


class GroupMemberUpdateRole(BaseModel):
    """Schema for updating member role"""
    role: MemberRole


class GroupConversationUpdate(BaseModel):
    """Schema for updating group conversation"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)

