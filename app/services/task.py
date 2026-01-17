from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.schemas.task import TaskCreate
from uuid import UUID

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
