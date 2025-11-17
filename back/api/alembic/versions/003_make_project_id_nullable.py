"""Make project_id nullable in group_conversations

Revision ID: 003
Revises: 002
Create Date: 2025-11-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'


def upgrade() -> None:
    # Make project_id nullable to support general group chats (not project-based)
    op.alter_column('group_conversations', 'project_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)


def downgrade() -> None:
    # Revert project_id to not nullable
    # Note: This will fail if there are any rows with NULL project_id
    op.alter_column('group_conversations', 'project_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)

