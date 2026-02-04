import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from app.models.task import Task, TaskStatus
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.services.notification_generator import NotificationGenerator


class TestNotificationGenerator:
    """Tests for the NotificationGenerator service."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def sample_task_due_soon(self):
        """Create a task with due date approaching."""
        return Task(
            id=uuid4(),
            user_id=uuid4(),
            title="Test Task",
            status=TaskStatus.TODO,
            due_date=datetime.now(timezone.utc) + timedelta(hours=12),
            deleted_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status_changed_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_stale_task(self):
        """Create a stale task (status unchanged for 10 days)."""
        return Task(
            id=uuid4(),
            user_id=uuid4(),
            title="Stale Task",
            status=TaskStatus.TODO,
            due_date=None,
            deleted_at=None,
            created_at=datetime.now(timezone.utc) - timedelta(days=15),
            updated_at=datetime.now(timezone.utc) - timedelta(days=10),
            status_changed_at=datetime.now(timezone.utc) - timedelta(days=10)
        )
    
    @pytest.mark.asyncio
    async def test_generate_due_date_notifications_creates_notification(self, mock_db, sample_task_due_soon):
        """Test that tasks with approaching due dates get notifications."""
        # Mock the database query to return our sample task
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_task_due_soon]
        mock_db.execute.return_value = mock_result
        
        count = await NotificationGenerator.generate_due_date_notifications(mock_db)
        
        assert count == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the notification was created correctly
        added_notification = mock_db.add.call_args[0][0]
        assert isinstance(added_notification, Notification)
        assert added_notification.type == NotificationType.DUE_DATE_APPROACHING
        assert added_notification.status == NotificationStatus.PENDING
        assert added_notification.task_id == sample_task_due_soon.id
        assert added_notification.user_id == sample_task_due_soon.user_id
    
    @pytest.mark.asyncio
    async def test_generate_due_date_notifications_no_tasks(self, mock_db):
        """Test that no notifications are created when no tasks match criteria."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        count = await NotificationGenerator.generate_due_date_notifications(mock_db)
        
        assert count == 0
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_stale_task_notifications_creates_notification(self, mock_db, sample_stale_task):
        """Test that stale tasks get notifications."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_stale_task]
        mock_db.execute.return_value = mock_result
        
        count = await NotificationGenerator.generate_stale_task_notifications(mock_db)
        
        assert count == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the notification was created correctly
        added_notification = mock_db.add.call_args[0][0]
        assert isinstance(added_notification, Notification)
        assert added_notification.type == NotificationType.STALE_TASK
        assert added_notification.status == NotificationStatus.PENDING
        assert added_notification.task_id == sample_stale_task.id
    
    @pytest.mark.asyncio
    async def test_generate_all_runs_both_generators(self, mock_db):
        """Test that generate_all runs both generators and returns combined results."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        result = await NotificationGenerator.generate_all(mock_db)
        
        assert "due_date_approaching" in result
        assert "stale_task" in result
        assert "total" in result
        assert result["total"] == result["due_date_approaching"] + result["stale_task"]
