from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.task import Task, TaskCreate, TaskUpdate
from app.services.task import TaskService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from uuid import UUID

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task for the authenticated user.
    """
    return await TaskService.create_task(db, task_in, current_user.id)

@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task for the authenticated user.
    """
    task = await TaskService.update_task(db, task_id, task_in, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or you don't have permission to access it"
        )
    return task
