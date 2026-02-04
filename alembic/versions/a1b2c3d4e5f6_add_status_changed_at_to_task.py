"""Add status_changed_at to task

Revision ID: a1b2c3d4e5f6
Revises: d2daf86a58de
Create Date: 2026-02-04 18:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd2daf86a58de'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status_changed_at column (nullable initially for backfill)
    op.add_column('task', sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Backfill existing rows with updated_at value
    op.execute("UPDATE task SET status_changed_at = updated_at WHERE status_changed_at IS NULL")
    
    # Set server default for future inserts
    op.alter_column('task', 'status_changed_at',
                    server_default=sa.text('now()'),
                    nullable=True)


def downgrade() -> None:
    op.drop_column('task', 'status_changed_at')
