import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
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

def test_delete_task_success(mock_user):
    task_id = uuid4()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.delete_task") as mock_delete:
        mock_delete.return_value = True
        
        response = client.delete(f"/tasks/{task_id}")
        
        assert response.status_code == 204
        
    app.dependency_overrides.clear()

def test_delete_task_not_found(mock_user):
    task_id = uuid4()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.delete_task") as mock_delete:
        mock_delete.return_value = False
        
        response = client.delete(f"/tasks/{task_id}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found or you don't have permission to access it"
        
    app.dependency_overrides.clear()

def test_update_deleted_task(mock_user):
    task_id = uuid4()
    update_data = {"title": "Updated Title"}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.update_task") as mock_update:
        # Service should return None if task is deleted or not found
        mock_update.return_value = None
        
        response = client.patch(f"/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 404
        
    app.dependency_overrides.clear()

def test_get_tasks_success(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.get_tasks") as mock_get:
        mock_tasks = [
            Task(
                id=uuid4(),
                title="Task 1",
                description="Description 1",
                user_id=mock_user.id,
                status=TaskStatus.TODO,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            Task(
                id=uuid4(),
                title="Task 2",
                description="Description 2",
                user_id=mock_user.id,
                status=TaskStatus.DONE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        mock_get.return_value = mock_tasks
        
        response = client.get("/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"
        
    app.dependency_overrides.clear()

def test_get_tasks_filter_by_status(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.get_tasks") as mock_get:
        # Mocking the service to return only 'todo' tasks when called with status=todo
        mock_tasks = [
            Task(
                id=uuid4(),
                title="Task 1",
                description="Description 1",
                user_id=mock_user.id,
                status=TaskStatus.TODO,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        mock_get.return_value = mock_tasks
        
        response = client.get("/tasks/?status=todo")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "todo"
        
        # Verify that the service was called with the correct status
        mock_get.assert_called_once()
        # The first argument is the DB session (MagicMock), second is user_id, third is status
        call_args = mock_get.call_args
        assert call_args[0][1] == mock_user.id
        assert call_args[0][2] == TaskStatus.TODO
        
    app.dependency_overrides.clear()
