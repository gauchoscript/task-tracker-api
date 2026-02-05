import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from app.models.task import Task, TaskStatus
from app.models.notification import Notification, NotificationType, NotificationStatus, DeviceToken
from app.services.notification_sender import NotificationSender
from app.core.config import settings


class TestNotificationSender:
    """Tests for the NotificationSender service."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def sample_notification(self):
        """Create a sample pending notification."""
        return Notification(
            id=uuid4(),
            user_id=uuid4(),
            task_id=uuid4(),
            type=NotificationType.DUE_DATE_APPROACHING,
            status=NotificationStatus.PENDING,
            scheduled_for=datetime.now(timezone.utc) - timedelta(minutes=5),
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for notification formatting."""
        return Task(
            id=uuid4(),
            user_id=uuid4(),
            title="Important Meeting Prep",
            status=TaskStatus.TODO,
            due_date=datetime.now(timezone.utc) + timedelta(hours=6),
            status_changed_at=datetime.now(timezone.utc) - timedelta(days=3)
        )
    
    @pytest.mark.asyncio
    async def test_get_pending_notifications(self, mock_db, sample_notification):
        """Test fetching pending notifications."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_notification]
        mock_db.execute.return_value = mock_result
        
        notifications = await NotificationSender.get_pending_notifications(mock_db)
        
        assert len(notifications) == 1
        assert notifications[0] == sample_notification
    
    @pytest.mark.asyncio
    async def test_get_device_tokens_for_user(self, mock_db):
        """Test fetching device tokens for a user."""
        user_id = uuid4()
        expected_tokens = ["token1", "token2"]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = expected_tokens
        mock_db.execute.return_value = mock_result
        
        tokens = await NotificationSender.get_device_tokens_for_user(mock_db, user_id)
        
        assert tokens == expected_tokens
    
    @pytest.mark.asyncio
    async def test_send_notification_no_tokens_fails(self, mock_db, sample_notification):
        """Test that sending fails when user has no device tokens."""
        # Mock no tokens
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        result = await NotificationSender.send_notification(mock_db, sample_notification)
        
        assert result is False
        assert sample_notification.status == NotificationStatus.FAILED
        assert "No device tokens" in sample_notification.error_message
    
    @pytest.mark.asyncio
    async def test_send_all_pending_respects_quiet_hours(self, mock_db):
        """Test that send_all_pending skips during quiet hours."""
        with patch.object(NotificationSender, 'is_quiet_hours', return_value=True):
            result = await NotificationSender.send_all_pending(mock_db)
        
        assert result["skipped_quiet_hours"] is True
        assert result["sent"] == 0
        assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_send_all_pending_processes_notifications(self, mock_db, sample_notification):
        """Test that send_all_pending processes pending notifications."""
        with patch.object(NotificationSender, 'is_quiet_hours', return_value=False):
            with patch.object(NotificationSender, 'get_pending_notifications', 
                            return_value=[sample_notification]):
                with patch.object(NotificationSender, 'send_notification', return_value=True):
                    result = await NotificationSender.send_all_pending(mock_db)
        
        assert result["skipped_quiet_hours"] is False
        assert result["sent"] == 1
