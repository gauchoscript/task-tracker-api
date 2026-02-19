"""add read columns to notification

Revision ID: 773c11550169
Revises: 57e10df06652
Create Date: 2026-02-18 20:54:50.469131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '773c11550169'
down_revision = '57e10df06652'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the Enum type for read_source
    read_source_type = sa.Enum('web_push', 'web_client', name='readsource')
    
    op.add_column('notification', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('notification', sa.Column('read_source', read_source_type, nullable=True))
    
    # Index for efficient unread filtering per user
    op.create_index('ix_notification_user_read', 'notification', ['user_id', 'read_at'])


def downgrade() -> None:
    op.drop_index('ix_notification_user_read', table_name='notification')
    op.drop_column('notification', 'read_source')
    op.drop_column('notification', 'read_at')
    
    # Drop the enum type
    sa.Enum(name='readsource').drop(op.get_bind(), checkfirst=True)
