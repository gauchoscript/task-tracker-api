from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, nullsfirst
from sqlalchemy.orm import joinedload
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from app.models.notification import DeviceToken, Notification, NotificationStatus, ReadSource, NotificationType
from app.models.task import Task
from app.schemas.notification import DeviceTokenCreate
from app.services.notification_templates import format_notification

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def register_device(
        db: AsyncSession, 
        device_in: DeviceTokenCreate, 
        user_id: UUID
    ) -> DeviceToken:
        """
        Register or update a device token for a user.
        If the token already exists for a different user, it reassigns it.
        """
        # Check if the token already exists
        query = select(DeviceToken).where(DeviceToken.token == device_in.token)
        result = await db.execute(query)
        db_device = result.scalar_one_or_none()
        
        if db_device:
            # Update existing registration
            db_device.user_id = user_id
            db_device.platform = device_in.platform
            db_device.updated_at = datetime.now(timezone.utc)
        else:
            # Create new registration
            db_device = DeviceToken(
                user_id=user_id,
                token=device_in.token,
                platform=device_in.platform
            )
            db.add(db_device)
            
        await db.commit()
        await db.refresh(db_device)
        return db_device

    @staticmethod
    async def unregister_device(
        db: AsyncSession,
        token: str,
        user_id: UUID
    ) -> bool:
        """
        Remove a device token for a user.
        """
        query = select(DeviceToken).where(
            DeviceToken.token == token,
            DeviceToken.user_id == user_id
        )
        result = await db.execute(query)
        db_device = result.scalar_one_or_none()
        
        if not db_device:
            return False
            
        await db.delete(db_device)
        await db.commit()
        return True

    @staticmethod
    async def get_notifications_for_user(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Notification]:
        """
        Get sent notifications for a user with pagination, unread ones first.
        Includes title and message populated from templates.
        """
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.SENT
        ).options(
            joinedload(Notification.task)
        ).order_by(
            nullsfirst(Notification.read_at),
            desc(Notification.created_at)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        notifications = list(result.scalars().all())
        
        valid_notifications = []
        
        # Populate title and message for each notification
        for n in notifications:
            if n.task:
                n.title, n.message = format_notification(n.type, n.task)
                valid_notifications.append(n)
            else:
                logger.error(f"Orphan notification found: {n.id} for user {user_id}. Task {n.task_id} is missing.")
                
        return valid_notifications

    @staticmethod
    async def mark_notification_read(
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
        read_source: ReadSource
    ) -> Optional[Notification]:
        """
        Mark a notification as read.
        Only marks if it belongs to the user and is not already read.
        """
        query = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            return None
            
        if not notification.read_at:
            notification.read_at = datetime.now(timezone.utc)
            notification.read_source = read_source
            await db.commit()
            await db.refresh(notification)
            
        return notification
