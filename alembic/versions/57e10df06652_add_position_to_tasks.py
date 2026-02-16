"""add position to tasks

Revision ID: 57e10df06652
Revises: b2c3d4e5f6a7
Create Date: 2026-02-15 23:11:54.037306

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57e10df06652'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('task', sa.Column('position', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('task', 'position')
