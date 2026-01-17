import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
from uuid import uuid4
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        external_id="fake-sub-123"
    )

def test_create_task_success(mock_user):
    # Mock data
    task_data = {
        "title": "Test Task",
        "description": "Test Description"
    }
    
    # Override the dependency to return our mock user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.create_task") as mock_create:
        # Mock the service return value
        mock_task = Task(
            id=uuid4(),
            title=task_data["title"],
            description=task_data["description"],
            user_id=mock_user.id,
            status=TaskStatus.TODO,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_create.return_value = mock_task
        
        response = client.post("/tasks/", json=task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
    # Clean up overrides
    app.dependency_overrides.clear()

def test_create_task_unauthorized():
    # Without overriding get_current_user, it should fail (or we can explicitly mock it to raise)
    # But usually, it fails because there's no token in the request.
    task_data = {
        "title": "Test Task",
        "description": "Test Description"
    }
    
    response = client.post("/tasks/", json=task_data)
    
    # Since OAuth2PasswordBearer is used, it should return 401 if no Authorization header is present
    assert response.status_code == 401

def test_update_task_success(mock_user):
    task_id = uuid4()
    update_data = {"title": "Updated Title", "status": "done"}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.update_task") as mock_update:
        mock_task = Task(
            id=task_id,
            title=update_data["title"],
            description="Old Description",
            user_id=mock_user.id,
            status=TaskStatus.DONE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_update.return_value = mock_task
        
        response = client.patch(f"/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["status"] == "done"
        
    app.dependency_overrides.clear()

def test_update_task_not_found(mock_user):
    task_id = uuid4()
    update_data = {"title": "Updated Title"}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.update_task") as mock_update:
        mock_update.return_value = None
        
        response = client.patch(f"/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found or you don't have permission to access it"
        
    app.dependency_overrides.clear()
