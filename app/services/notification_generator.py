"""
NotificationGenerator service.
Detects conditions that should trigger notifications and inserts them into the outbox.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, not_, exists
from app.models.task import Task, TaskStatus
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.core.config import settings
from datetime import datetime, timezone, timedelta
from typing import List
import logging

logger = logging.getLogger(__name__)


class NotificationGenerator:
    """
    Generates notifications based on task conditions.
    Each generator method checks for specific conditions and creates
    pending notifications in the outbox (notification table).
    """
    
    @staticmethod
    async def generate_due_date_notifications(db: AsyncSession) -> int:
        """
        Generate notifications for tasks approaching their due date.
        
        Returns:
            Number of notifications created
        """
        threshold = datetime.now(timezone.utc) + timedelta(
            days=settings.NOTIFICATION_DUE_DATE_DAYS_BEFORE
        )
        
        # Subquery to check for existing pending notification of same type
        existing_notification = select(Notification.id).where(
            and_(
                Notification.task_id == Task.id,
                Notification.type == NotificationType.DUE_DATE_APPROACHING,
                Notification.status == NotificationStatus.PENDING
            )
        ).correlate(Task)
        
        # Find tasks with due dates within threshold, not done, no pending notification
        query = select(Task).where(
            and_(
                Task.due_date != None,
                Task.due_date <= threshold,
                Task.due_date > datetime.now(timezone.utc),
                Task.status != TaskStatus.DONE,
                Task.deleted_at == None,
                ~exists(existing_notification)
            )
        )
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        created_count = 0
        for task in tasks:
            notification = Notification(
                user_id=task.user_id,
                task_id=task.id,
                type=NotificationType.DUE_DATE_APPROACHING,
                status=NotificationStatus.PENDING,
                scheduled_for=datetime.now(timezone.utc)
            )
            db.add(notification)
            created_count += 1
            logger.info(f"Created due_date_approaching notification for task {task.id}")
        
        if created_count > 0:
            await db.commit()
            
        return created_count
    
    @staticmethod
    async def generate_stale_task_notifications(db: AsyncSession) -> int:
        """
        Generate notifications for tasks that haven't had a status change in X days.
        
        Returns:
            Number of notifications created
        """
        threshold = datetime.now(timezone.utc) - timedelta(
            days=settings.NOTIFICATION_STALE_TASK_DAYS
        )
        
        # Subquery to check for existing pending notification of same type
        existing_notification = select(Notification.id).where(
            and_(
                Notification.task_id == Task.id,
                Notification.type == NotificationType.STALE_TASK,
                Notification.status == NotificationStatus.PENDING
            )
        ).correlate(Task)
        
        # Find tasks in TODO status unchanged for too long
        query = select(Task).where(
            and_(
                Task.status == TaskStatus.TODO,
                Task.status_changed_at != None,
                Task.status_changed_at < threshold,
                Task.deleted_at == None,
                ~exists(existing_notification)
            )
        )
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        created_count = 0
        for task in tasks:
            notification = Notification(
                user_id=task.user_id,
                task_id=task.id,
                type=NotificationType.STALE_TASK,
                status=NotificationStatus.PENDING,
                scheduled_for=datetime.now(timezone.utc)
            )
            db.add(notification)
            created_count += 1
            logger.info(f"Created stale_task notification for task {task.id}")
        
        if created_count > 0:
            await db.commit()
            
        return created_count
    
    @staticmethod
    async def generate_all(db: AsyncSession) -> dict:
        """
        Run all notification generators.
        
        Returns:
            Dictionary with count of notifications created by each generator
        """
        due_date_count = await NotificationGenerator.generate_due_date_notifications(db)
        stale_count = await NotificationGenerator.generate_stale_task_notifications(db)
        
        return {
            "due_date_approaching": due_date_count,
            "stale_task": stale_count,
            "total": due_date_count + stale_count
        }
