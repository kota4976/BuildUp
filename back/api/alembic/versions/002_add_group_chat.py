"""Add group chat tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'


def upgrade() -> None:
    # Create group_conversations table
    op.create_table(
        'group_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_unique_constraint('uq_group_conversations_project', 'group_conversations', ['project_id'])
    
    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('group_conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('owner', 'member', name='memberrole'), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('group_conversation_id', 'user_id'),
        sa.ForeignKeyConstraint(['group_conversation_id'], ['group_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create group_messages table
    op.create_table(
        'group_messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('group_conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_conversation_id'], ['group_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
    )
    op.create_index('idx_group_messages_conv_time', 'group_messages', ['group_conversation_id', 'created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_group_messages_conv_time', table_name='group_messages')
    op.drop_table('group_messages')
    op.drop_table('group_members')
    op.drop_table('group_conversations')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS memberrole')

