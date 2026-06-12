"""Add telegram_id and telegram_username to users

Revision ID: 001
Revises: 
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('telegram_id', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('telegram_username', sa.String(64), nullable=True))
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_users_telegram_id', 'users')
    op.drop_column('users', 'telegram_username')
    op.drop_column('users', 'telegram_id')
