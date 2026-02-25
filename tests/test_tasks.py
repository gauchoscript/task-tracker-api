import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession
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
        "description": "Test Description",
        "due_date": "2026-12-31T23:59:59"
    }
    
    # Override the dependency to return our mock user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.create_task") as mock_create:
        # Mock the service return value
        mock_task = Task(
            id=uuid4(),
            title=task_data["title"],
            description=task_data["description"],
            due_date=datetime.fromisoformat(task_data["due_date"]),
            user_id=mock_user.id,
            status=TaskStatus.TODO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_create.return_value = mock_task
        
        response = client.post("/tasks", json=task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["due_date"] == task_data["due_date"]
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
    
    response = client.post("/tasks", json=task_data)
    
    # Since OAuth2PasswordBearer is used, it should return 401 if no Authorization header is present
    assert response.status_code == 401

def test_update_task_success(mock_user):
    task_id = uuid4()
    update_data = {
        "title": "Updated Title", 
        "status": "done",
        "due_date": "2026-06-01T00:00:00"
    }
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.update_task") as mock_update:
        mock_task = Task(
            id=task_id,
            title=update_data["title"],
            description="Old Description",
            due_date=datetime.fromisoformat(update_data["due_date"]),
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
        assert data["due_date"] == update_data["due_date"]
        
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
        
        response = client.get("/tasks")
        
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
        
        response = client.get("/tasks?status=todo")
        
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

def test_move_task_success(mock_user):
    task_id = uuid4()
    above_id = uuid4()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.move_task") as mock_move:
        mock_task = Task(
            id=task_id,
            title="Moved Task",
            user_id=mock_user.id,
            position=1500,
            status=TaskStatus.TODO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_move.return_value = mock_task
        
        response = client.patch(f"/tasks/{task_id}/move", json={"above_id": str(above_id)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task_id)
        assert data["position"] == 1500
        mock_move.assert_called_once()
        
    app.dependency_overrides.clear()

def test_move_task_failure(mock_user):
    task_id = uuid4()
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("app.services.task.TaskService.move_task") as mock_move:
        mock_move.return_value = None
        
        response = client.patch(f"/tasks/{task_id}/move", json={})
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Could not move task. Ensure the IDs are valid and belong to you."
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_task_position_logic():
    from app.services.task import TaskService
    
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid4()
    
    # Mock result and scalar
    mock_result = MagicMock()
    db.execute.return_value = mock_result
    
    # Case 1: First task for user
    mock_result.scalar.return_value = None
    task_in = MagicMock(title="Task 1", description=None, due_date=None)
    
    task = await TaskService.create_task(db, task_in, user_id)
    assert task.position == 0
    
    # Case 2: Subsequent tasks
    mock_result.scalar.return_value = 1000
    task_in = MagicMock(title="Task 2", description=None, due_date=None)
    
    task = await TaskService.create_task(db, task_in, user_id)
    assert task.position == 2000

@pytest.mark.asyncio
async def test_move_task_gap_logic():
    from app.services.task import TaskService
    
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid4()
    task_id = uuid4()
    above_id = uuid4()
    below_id = uuid4()
    
    # helper to produce result mocks
    def get_mock_result(val):
        m = MagicMock()
        m.scalar_one_or_none.return_value = val
        m.scalar.return_value = val
        return m

    # Test 1: Move between two tasks
    task_to_move = Task(id=task_id, user_id=user_id, position=1000)
    db.execute.side_effect = [
        get_mock_result(task_to_move),
        get_mock_result(3000), # pos_above
        get_mock_result(2000), # pos_below
    ]
    
    task = await TaskService.move_task(db, task_id, user_id, above_id=above_id, below_id=below_id)
    assert task.position == 2500  # (3000 + 2000) // 2
    
    # Test 2: Move to the top (above is None)
    task_to_move = Task(id=task_id, user_id=user_id, position=2500)
    db.execute.side_effect = [
        get_mock_result(task_to_move),
        get_mock_result(2000), # pos_below
    ]
    task = await TaskService.move_task(db, task_id, user_id, above_id=None, below_id=below_id)
    assert task.position == 3000  # 2000 + 1000
    
    # Test 3: Move to the bottom (below is None)
    task_to_move = Task(id=task_id, user_id=user_id, position=3000)
    db.execute.side_effect = [
        get_mock_result(task_to_move),
        get_mock_result(3000), # pos_above
    ]
    task = await TaskService.move_task(db, task_id, user_id, above_id=above_id, below_id=None)
    assert task.position == 2000  # 3000 - 1000
