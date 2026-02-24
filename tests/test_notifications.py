import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import DeviceToken, Notification, NotificationType, NotificationStatus, ReadSource
from app.models.task import Task
from sqlalchemy.orm import RelationshipProperty
from uuid import uuid4
from datetime import datetime, timezone

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        external_id="fake-sub-123"
    )

def test_register_device_success(mock_user):
    device_data = {
        "token": "fake-fcm-token-123",
        "platform": "web"
    }
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.register_device") as mock_register:
        mock_device = DeviceToken(
            id=uuid4(),
            user_id=mock_user.id,
            token=device_data["token"],
            platform=device_data["platform"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_register.return_value = mock_device
        
        response = client.post("/notifications/devices", json=device_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["token"] == device_data["token"]
        assert data["platform"] == device_data["platform"]
        assert "id" in data
        
    app.dependency_overrides.clear()

def test_register_device_update(mock_user):
    # This test simulates calling the register endpoint for a token that already exists
    device_data = {
        "token": "existing-token-123",
        "platform": "ios"
    }
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.register_device") as mock_register:
        mock_device = DeviceToken(
            id=uuid4(),
            user_id=mock_user.id,
            token=device_data["token"],
            platform=device_data["platform"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_register.return_value = mock_device
        
        response = client.post("/notifications/devices", json=device_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["token"] == device_data["token"]
        assert data["platform"] == "ios"
        
    app.dependency_overrides.clear()

def test_register_device_missing_platform(mock_user):
    device_data = {
        "token": "fake-fcm-token-123"
        # platform missing
    }
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    response = client.post("/notifications/devices", json=device_data)
    
    # Pydantic should validation error (422 Unprocessable Entity)
    assert response.status_code == 422
    
    app.dependency_overrides.clear()

def test_unregister_device_success(mock_user):
    token = "fake-fcm-token-123"
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.unregister_device") as mock_unregister:
        mock_unregister.return_value = True
        
        response = client.delete(f"/notifications/devices/{token}")
        
        assert response.status_code == 204
        
    app.dependency_overrides.clear()

def test_unregister_device_not_found(mock_user):
    token = "non-existent-token"
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.unregister_device") as mock_unregister:
        mock_unregister.return_value = False
        
        response = client.delete(f"/notifications/devices/{token}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Device token not found for this user"
        
    app.dependency_overrides.clear()

def test_list_notifications_success(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.get_notifications_for_user") as mock_get:
        mock_notifications = [
            Notification(
                id=uuid4(),
                type=NotificationType.DUE_DATE_APPROACHING,
                read_at=None,
                sent_at=datetime.now(timezone.utc)
            ),
            Notification(
                id=uuid4(),
                type=NotificationType.STALE_TASK,
                read_at=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc)
            )
        ]
        # Manually add title/message as the service would
        mock_notifications[0].title = "Task due soon"
        mock_notifications[0].message = "Test message 1"
        mock_notifications[1].title = "Task needs attention"
        mock_notifications[1].message = "Test message 2"
        
        mock_get.return_value = (mock_notifications, 2)
        
        response = client.get("/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["read_at"] is None
        assert data["items"][0]["title"] == "Task due soon"
        assert data["items"][0]["message"] == "Test message 1"
        assert "user_id" not in data["items"][0]
        assert "status" not in data["items"][0]
        
    app.dependency_overrides.clear()

def test_mark_notification_read_success(mock_user):
    notification_id = uuid4()
    read_data = {"read_source": "web_client"}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.mark_notification_read") as mock_mark:
        mock_notification = Notification(
            id=notification_id,
            type=NotificationType.DUE_DATE_APPROACHING,
            read_at=datetime.now(timezone.utc),
            sent_at=datetime.now(timezone.utc)
        )
        mock_notification.title = "Task due soon"
        mock_notification.message = "Test message"
        mock_mark.return_value = mock_notification
        
        response = client.patch(f"/notifications/{notification_id}/read", json=read_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["read_at"] is not None
        
    app.dependency_overrides.clear()

def test_mark_notification_read_not_found(mock_user):
    notification_id = uuid4()
    read_data = {"read_source": "web_push"}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.mark_notification_read") as mock_mark:
        mock_mark.return_value = None
        
        response = client.patch(f"/notifications/{notification_id}/read", json=read_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Notification not found"
        
    app.dependency_overrides.clear()

def test_mark_notification_read_invalid_id(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    response = client.patch("/notifications/invalid-uuid/read", json={"read_source": "web_push"})
    
    # FastAPI returns 422 for validation errors (like invalid UUID format)
    assert response.status_code == 422
    
    app.dependency_overrides.clear()

def test_list_notifications_pagination(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.notification.NotificationService.get_notifications_for_user") as mock_get:
        # Mocking 2 notifications
        mock_notifications = [
            Notification(id=uuid4(), type=NotificationType.DUE_DATE_APPROACHING, read_at=None, sent_at=datetime.now(timezone.utc)),
            Notification(id=uuid4(), type=NotificationType.STALE_TASK, read_at=None, sent_at=datetime.now(timezone.utc))
        ]
        for n in mock_notifications:
            n.title = "Title"
            n.message = "Message"
            
        mock_get.return_value = (mock_notifications, 100)
        
        # Test default skip/limit
        response = client.get("/notifications/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["skip"] == 0
        assert data["limit"] == 20
        # The mock_get call might use positional or keyword args, using call_args is safer or checking the patch call
        
        # Test custom skip/limit
        response = client.get("/notifications/?skip=10&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["skip"] == 10
        assert data["limit"] == 5
        # Use ANY for the AsyncSession argument
    mock_get.assert_called_with(ANY, mock_user.id, skip=10, limit=5)
    
    app.dependency_overrides.clear()

def test_notification_task_relationship_defined():
    """
    Verifies that the SQLAlchemy relationships are correctly defined on the models.
    """
    # Check Notification.task
    assert hasattr(Notification, "task")
    assert isinstance(Notification.task.property, RelationshipProperty)
    assert Notification.task.property.target.name == "task"
    
    # Check that Task does NOT have notifications (unidirectional)
    assert not hasattr(Task, "notifications")
