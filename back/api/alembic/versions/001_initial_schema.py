"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-11-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')
    
    # Create IMMUTABLE wrapper for unaccent function (required for index)
    op.execute("""
        CREATE OR REPLACE FUNCTION unaccent_immutable(text)
        RETURNS text AS $$
        SELECT unaccent('unaccent', $1);
        $$ LANGUAGE sql IMMUTABLE;
    """)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('handle', sa.Text(), nullable=False),
        sa.Column('email', sa.Text()),
        sa.Column('avatar_url', sa.Text()),
        sa.Column('bio', sa.Text()),
        sa.Column('github_login', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint('uq_users_handle', 'users', ['handle'])
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    op.create_unique_constraint('uq_users_github_login', 'users', ['github_login'])
    op.create_index('idx_users_handle', 'users', ['handle'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_github_login', 'users', ['github_login'])
    
    # Create oauth_accounts table
    op.create_table(
        'oauth_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('provider_account_id', sa.Text(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_unique_constraint('uq_provider_account', 'oauth_accounts', ['provider', 'provider_account_id'])
    
    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.Text(), nullable=False),
    )
    op.create_unique_constraint('uq_skills_name', 'skills', ['name'])
    op.create_index('idx_skills_name', 'skills', ['name'])
    
    # Create user_skills table
    op.create_table(
        'user_skills',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.SmallInteger()),
        sa.CheckConstraint('level BETWEEN 1 AND 5', name='ck_user_skills_level'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'skill_id')
    )
    
    # Create github_repos table
    op.create_table(
        'github_repos',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repo_full_name', sa.Text(), nullable=False),
        sa.Column('stars', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('language', sa.Text()),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('last_pushed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_unique_constraint('uq_user_repo', 'github_repos', ['user_id', 'repo_full_name'])
    
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
    )
    
    # Create full-text search index for projects
    op.execute("""
        CREATE INDEX idx_projects_search ON projects 
        USING GIN (to_tsvector('simple', unaccent_immutable(coalesce(title,'')||' '||coalesce(description,''))))
    """)
    
    # Create project_skills table
    op.create_table(
        'project_skills',
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('required_level', sa.SmallInteger()),
        sa.CheckConstraint('required_level BETWEEN 1 AND 5', name='ck_project_skills_required_level'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id', 'skill_id')
    )
    
    # Create favorites table
    op.create_table(
        'favorites',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'project_id')
    )
    
    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('applicant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id']),
    )
    op.create_unique_constraint('uq_project_applicant', 'applications', ['project_id', 'applicant_id'])
    
    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id']),
    )
    op.create_unique_constraint('uq_project_sender_receiver', 'offers', ['project_id', 'sender_id', 'receiver_id'])
    
    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_a', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_b', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_a'], ['users.id']),
        sa.ForeignKeyConstraint(['user_b'], ['users.id']),
    )
    op.create_unique_constraint('uq_project_users', 'matches', ['project_id', 'user_a', 'user_b'])
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
    )
    op.create_index('idx_messages_conv_time', 'messages', ['conversation_id', 'created_at'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('resource', sa.Text()),
        sa.Column('payload', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('matches')
    op.drop_table('offers')
    op.drop_table('applications')
    op.drop_table('favorites')
    op.drop_table('project_skills')
    op.drop_table('projects')
    op.drop_table('github_repos')
    op.drop_table('user_skills')
    op.drop_table('skills')
    op.drop_table('oauth_accounts')
    op.drop_table('users')
    
    # Drop custom function
    op.execute('DROP FUNCTION IF EXISTS unaccent_immutable(text)')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS unaccent')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

