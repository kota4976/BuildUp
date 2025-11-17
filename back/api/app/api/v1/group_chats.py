"""Group chat endpoints"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.group_chat import GroupConversation, GroupMember, GroupMessage, MemberRole
from app.schemas.group_chat import (
    GroupConversationCreate,
    GeneralGroupCreate,
    GroupConversationResponse,
    GroupConversationDetailResponse,
    GroupConversationUpdate,
    GroupMessageResponse,
    GroupMemberAdd,
    GroupMemberUpdateRole,
)
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/general", response_model=GroupConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_general_group(
    data: GeneralGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a general group conversation (not project-based)
    
    The creator is automatically added as a member with owner role.
    Additional members specified in member_ids are added with member role.
    
    Args:
        data: General group creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created group conversation
    """
    # Validate that all member IDs exist and are not deleted
    members_to_add = db.query(User).filter(
        User.id.in_(data.member_ids),
        User.deleted_at.is_(None)
    ).all()
    
    if len(members_to_add) != len(data.member_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more user IDs are invalid"
        )
    
    # Create group conversation
    group_conv = GroupConversation(
        project_id=None,  # General group, not project-based
        name=data.name
    )
    db.add(group_conv)
    db.flush()
    
    # Add creator as owner
    owner_member = GroupMember(
        group_conversation_id=group_conv.id,
        user_id=current_user.id,
        role=MemberRole.owner
    )
    db.add(owner_member)
    
    # Add other members
    for user in members_to_add:
        # Skip if user is the creator (already added as owner)
        if user.id == current_user.id:
            continue
        
        member = GroupMember(
            group_conversation_id=group_conv.id,
            user_id=user.id,
            role=MemberRole.member
        )
        db.add(member)
    
    db.commit()
    db.refresh(group_conv)
    
    return GroupConversationResponse.from_orm(group_conv)


@router.post("", response_model=GroupConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_group_conversation(
    data: GroupConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a group conversation for a project
    
    Only the project owner can create a group conversation.
    The owner is automatically added as a member with owner role.
    
    Args:
        data: Group conversation creation data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created group conversation
    """
    # Check if project exists and user is owner
    project = db.query(Project).filter(Project.id == data.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can create group conversation"
        )
    
    # Check if group conversation already exists for this project
    existing = db.query(GroupConversation).filter(
        GroupConversation.project_id == data.project_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group conversation already exists for this project"
        )
    
    # Create group conversation
    group_conv = GroupConversation(
        project_id=data.project_id,
        name=data.name
    )
    db.add(group_conv)
    db.flush()
    
    # Add owner as member
    member = GroupMember(
        group_conversation_id=group_conv.id,
        user_id=current_user.id,
        role=MemberRole.owner
    )
    db.add(member)
    db.commit()
    db.refresh(group_conv)
    
    return GroupConversationResponse.from_orm(group_conv)


@router.get("", response_model=List[GroupConversationResponse])
async def get_my_group_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all group conversations the current user is a member of
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of group conversations
    """
    # Get group conversations where user is a member
    group_convs = db.query(GroupConversation).join(
        GroupMember,
        GroupConversation.id == GroupMember.group_conversation_id
    ).filter(
        GroupMember.user_id == current_user.id
    ).options(
        joinedload(GroupConversation.members)
    ).order_by(GroupConversation.updated_at.desc()).all()
    
    return [GroupConversationResponse.from_orm(gc) for gc in group_convs]


@router.get("/{group_conversation_id}", response_model=GroupConversationDetailResponse)
async def get_group_conversation(
    group_conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    before_id: int = Query(None, description="Get messages before this ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get group conversation with messages
    
    Args:
        group_conversation_id: Group conversation ID
        limit: Maximum number of messages
        before_id: Get messages before this message ID (for pagination)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Group conversation with messages
    """
    # Get group conversation
    group_conv = db.query(GroupConversation).filter(
        GroupConversation.id == group_conversation_id
    ).options(
        joinedload(GroupConversation.members)
    ).first()
    
    if not group_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group conversation not found"
        )
    
    # Check if user is a member
    is_member = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conversation_id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this group conversation"
        )
    
    # Get messages
    q = db.query(GroupMessage).filter(
        GroupMessage.group_conversation_id == group_conversation_id
    )
    
    if before_id:
        q = q.filter(GroupMessage.id < before_id)
    
    messages = q.order_by(GroupMessage.created_at.desc()).limit(limit + 1).all()
    
    # Check if there are more messages
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]
    
    # Reverse to show oldest first
    messages.reverse()
    
    return GroupConversationDetailResponse(
        id=group_conv.id,
        project_id=group_conv.project_id,
        name=group_conv.name,
        created_at=group_conv.created_at,
        updated_at=group_conv.updated_at,
        members=[member for member in group_conv.members],
        messages=[GroupMessageResponse.from_orm(msg) for msg in messages],
        has_more=has_more
    )


@router.patch("/{group_conversation_id}", response_model=GroupConversationResponse)
async def update_group_conversation(
    group_conversation_id: str,
    data: GroupConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update group conversation (name)
    
    Only the owner can update the group conversation.
    
    Args:
        group_conversation_id: Group conversation ID
        data: Update data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated group conversation
    """
    # Get group conversation
    group_conv = db.query(GroupConversation).filter(
        GroupConversation.id == group_conversation_id
    ).first()
    
    if not group_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group conversation not found"
        )
    
    # Check if user is owner
    member = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conversation_id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if not member or member.role != MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can update group conversation"
        )
    
    # Update fields
    if data.name is not None:
        group_conv.name = data.name
    
    db.commit()
    db.refresh(group_conv)
    
    return GroupConversationResponse.from_orm(group_conv)


@router.post("/{group_conversation_id}/members", response_model=SuccessResponse)
async def add_member_to_group(
    group_conversation_id: str,
    data: GroupMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a member to the group conversation
    
    Only the owner can add members.
    
    Args:
        group_conversation_id: Group conversation ID
        data: Member data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Get group conversation
    group_conv = db.query(GroupConversation).filter(
        GroupConversation.id == group_conversation_id
    ).first()
    
    if not group_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group conversation not found"
        )
    
    # Check if current user is owner
    current_member = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conversation_id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if not current_member or current_member.role != MemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can add members"
        )
    
    # Check if user to add exists
    user_to_add = db.query(User).filter(User.id == data.user_id).first()
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already a member
    existing = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conversation_id,
            GroupMember.user_id == data.user_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )
    
    # Add member
    member = GroupMember(
        group_conversation_id=group_conversation_id,
        user_id=data.user_id,
        role=MemberRole.member
    )
    db.add(member)
    db.commit()
    
    return SuccessResponse(message="Member added successfully")


@router.delete("/{group_conversation_id}/members/{user_id}", response_model=SuccessResponse)
async def remove_member_from_group(
    group_conversation_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from the group conversation
    
    Owner can remove any member. Members can remove themselves.
    
    Args:
        group_conversation_id: Group conversation ID
        user_id: User ID to remove
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Get group conversation
    group_conv = db.query(GroupConversation).filter(
        GroupConversation.id == group_conversation_id
    ).first()
    
    if not group_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group conversation not found"
        )
    
    # Check if current user is owner or removing themselves
    current_member = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conversation_id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if not current_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )
    
    is_owner = current_member.role == MemberRole.owner
    is_self_removal = str(current_user.id) == user_id
    
    if not is_owner and not is_self_removal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this member"
        )
    
    # Get member to remove
    member_to_remove = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conversation_id,
            GroupMember.user_id == user_id
        )
    ).first()
    
    if not member_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot remove the owner
    if member_to_remove.role == MemberRole.owner and not is_self_removal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner"
        )
    
    db.delete(member_to_remove)
    db.commit()
    
    return SuccessResponse(message="Member removed successfully")


@router.get("/projects/{project_id}/group-conversation", response_model=GroupConversationResponse)
async def get_project_group_conversation(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the group conversation for a project
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Group conversation
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get group conversation
    group_conv = db.query(GroupConversation).filter(
        GroupConversation.project_id == project_id
    ).options(
        joinedload(GroupConversation.members)
    ).first()
    
    if not group_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group conversation not found for this project"
        )
    
    # Check if user is a member
    is_member = db.query(GroupMember).filter(
        and_(
            GroupMember.group_conversation_id == group_conv.id,
            GroupMember.user_id == current_user.id
        )
    ).first()
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this group conversation"
        )
    
    return GroupConversationResponse.from_orm(group_conv)

