from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.task import Task, TaskCreate, TaskUpdate, TaskMove
from app.services.task import TaskService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import TaskStatus
from typing import List, Optional
from uuid import UUID

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[Task])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks for the authenticated user, optionally filtered by status.
    """
    return await TaskService.get_tasks(db, current_user.id, status)

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

@router.patch("/{task_id}/move", response_model=Task)
async def move_task(
    task_id: UUID,
    move_in: TaskMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Move a task relative to other tasks.
    Provide above_id to place below it, or below_id to place above it.
    If both provided, place between them.
    """
    task = await TaskService.move_task(db, task_id, current_user.id, move_in.above_id, move_in.below_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not move task. Ensure the IDs are valid and belong to you."
        )
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete a task for the authenticated user.
    """
    success = await TaskService.delete_task(db, task_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or you don't have permission to access it"
        )
    return None
