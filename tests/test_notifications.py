import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import DeviceToken
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
