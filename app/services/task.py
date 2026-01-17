from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from uuid import UUID
from typing import Optional

class TaskService:
    @staticmethod
    async def create_task(db: AsyncSession, task_in: TaskCreate, user_id: UUID) -> Task:
        """
        Create a new task for a user.
        """
        db_task = Task(
            title=task_in.title,
            description=task_in.description,
            user_id=user_id
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
        Update an existing task if it belongs to the user.
        """
        query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(query)
        db_task = result.scalar_one_or_none()
        
        if not db_task:
            return None
            
        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
            
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return db_task
