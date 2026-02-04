"""Create notification table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-04 18:59:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('notification',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.Enum('due_date_approaching', 'stale_task', name='notificationtype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'sent', 'failed', name='notificationstatus'), server_default='pending', nullable=True),

        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for efficient querying of pending notifications
    op.create_index('ix_notification_status_scheduled', 'notification', ['status', 'scheduled_for'])
    # Index for deduplication checks
    op.create_index('ix_notification_task_type_status', 'notification', ['task_id', 'type', 'status'])


def downgrade() -> None:
    op.drop_index('ix_notification_task_type_status', table_name='notification')
    op.drop_index('ix_notification_status_scheduled', table_name='notification')
    op.drop_table('notification')
    
    # Drop enums
    sa.Enum(name='notificationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='notificationtype').drop(op.get_bind(), checkfirst=True)
