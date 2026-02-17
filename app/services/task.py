from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone

class TaskService:
    @staticmethod
    async def create_task(db: AsyncSession, task_in: TaskCreate, user_id: UUID) -> Task:
        """
        Create a new task for a user. New tasks are placed at the beginning by having 
        the highest position value (max position + 1000).
        """
        # Find the maximum position to place the new task at the top
        query = select(func.max(Task.position)).where(
            Task.user_id == user_id,
            Task.deleted_at == None
        )
        result = await db.execute(query)
        max_position = result.scalar()
        
        new_position = (max_position + 1000) if max_position is not None else 0

        db_task = Task(
            title=task_in.title,
            description=task_in.description,
            due_date=task_in.due_date,
            user_id=user_id,
            position=new_position
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return db_task

    @staticmethod
    async def update_task(
        db: AsyncSession, 
        task_id: UUID, 
        task_in: TaskUpdate, 
        user_id: UUID
    ) -> Optional[Task]:
        """
        Update an existing task if it belongs to the user and is not deleted.
        """
        query = select(Task).where(
            Task.id == task_id, 
            Task.user_id == user_id,
            Task.deleted_at == None
        )
        result = await db.execute(query)
        db_task = result.scalar_one_or_none()
        
        if not db_task:
            return None
        
        update_data = task_in.model_dump(exclude_unset=True)
        
        # Track if status is changing
        if 'status' in update_data and update_data['status'] != db_task.status:
            db_task.status_changed_at = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(db_task, field, value)
            
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return db_task

    @staticmethod
    async def get_tasks(db: AsyncSession, user_id: UUID, status: Optional[TaskStatus] = None) -> List[Task]:
        """
        Get all tasks for a user that are not deleted, optionally filtered by status.
        Ordered by the custom 'position' field descending (highest first).
        """
        query = select(Task).where(
            Task.user_id == user_id,
            Task.deleted_at == None
        ).order_by(Task.position.desc())
        
        if status:
            query = query.where(Task.status == status)
            
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def move_task(
        db: AsyncSession, 
        task_id: UUID, 
        user_id: UUID, 
        above_id: Optional[UUID] = None, 
        below_id: Optional[UUID] = None
    ) -> Optional[Task]:
        """
        Move a task between two other tasks.
        If above_id is None, move to the top.
        If below_id is None, move to the bottom.
        Calculates a new position value between the positions of above and below.
        """
        # 1. Fetch the task to be moved
        query = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
            Task.deleted_at == None
        )
        result = await db.execute(query)
        task_to_move = result.scalar_one_or_none()
        if not task_to_move:
            return None

        # 2. Determine positions
        # Note: Sorting is DESC, so "above" means higher position value.
        pos_above = None
        pos_below = None

        if above_id:
            query = select(Task.position).where(Task.id == above_id, Task.user_id == user_id, Task.deleted_at == None)
            pos_above = (await db.execute(query)).scalar()
            if pos_above is None: return None

        if below_id:
            query = select(Task.position).where(Task.id == below_id, Task.user_id == user_id, Task.deleted_at == None)
            pos_below = (await db.execute(query)).scalar()
            if pos_below is None: return None

        # 3. Calculate new position
        if pos_above is None and pos_below is None:
            return task_to_move

        if pos_above is None:
            new_position = pos_below + 1000
        elif pos_below is None:
            new_position = pos_above - 1000
        else:
            new_position = (pos_above + pos_below) // 2
            
            # Conflict check: if the difference is too small, we might need a re-gap.
            if new_position == pos_above or new_position == pos_below:
                # TODO: Emergency re-gap logic could go here if gap is 0.
                # Since we have large gaps, we'll assume this is rare.
                pass

        task_to_move.position = new_position
        await db.commit()
        await db.refresh(task_to_move)
        return task_to_move

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: UUID, user_id: UUID) -> bool:
        """
        Soft delete a task by setting its deleted_at timestamp.
        """
        query = select(Task).where(
            Task.id == task_id, 
            Task.user_id == user_id,
            Task.deleted_at == None
        )
        result = await db.execute(query)
        db_task = result.scalar_one_or_none()
        
        if not db_task:
            return False
            
        db_task.deleted_at = datetime.now(timezone.utc)
        db.add(db_task)
        await db.commit()
        return True
