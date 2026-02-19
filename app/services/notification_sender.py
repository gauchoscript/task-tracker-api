"""
NotificationSender service.
Processes pending notifications from the outbox and sends them via FCM.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.notification import DeviceToken
from app.models.task import Task
from app.services.notification_templates import format_notification
from app.core.config import settings
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import logging
import traceback

logger = logging.getLogger(__name__)

# Optional FCM import - will be None if firebase-admin is not installed
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False
    logger.warning("firebase-admin not installed, FCM sending disabled")


class NotificationSender:
    """
    Sends pending notifications from the outbox via FCM.
    Respects quiet hours and handles errors gracefully.
    """
    
    _fcm_initialized = False
    
    @classmethod
    def _initialize_fcm(cls):
        """Initialize Firebase Admin SDK if not already done."""
        if cls._fcm_initialized or not FCM_AVAILABLE:
            return
            
        if settings.FCM_CREDENTIALS_PATH:
            try:
                cred = credentials.Certificate(settings.FCM_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                cls._fcm_initialized = True
                logger.info("FCM initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FCM: {e}")
    
    @staticmethod
    def is_quiet_hours() -> bool:
        """Check if current time is within quiet hours."""
        current_hour = datetime.now().hour
        start = settings.NOTIFICATION_QUIET_HOURS_START
        end = settings.NOTIFICATION_QUIET_HOURS_END
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start > end:
            return current_hour >= start or current_hour < end
        else:
            return start <= current_hour < end
    
    @staticmethod
    async def get_pending_notifications(db: AsyncSession) -> List[Notification]:
        """Get all pending notifications ready to be sent."""
        query = select(Notification).where(
            and_(
                Notification.status == NotificationStatus.PENDING,
                Notification.scheduled_for <= datetime.now(timezone.utc)
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_device_tokens_for_user(db: AsyncSession, user_id) -> List[str]:
        """Get all device tokens for a user."""
        query = select(DeviceToken.token).where(DeviceToken.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_task(db: AsyncSession, task_id) -> Optional[Task]:
        """Get a task by ID."""
        if task_id is None:
            return None
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    def _send_fcm_message(
        cls, 
        tokens: List[str], 
        title: str, 
        body: str, 
        data: Optional[dict] = None
    ) -> tuple[int, int, Optional[str]]:
        """
        Send FCM message to multiple tokens.
        
        Returns:
            Tuple of (success_count, failure_count, error_message)
        """
        if not FCM_AVAILABLE or not cls._fcm_initialized:
            logger.warning("FCM not available, skipping send")
            return (0, 0, "FCM not configured")
        
        if not tokens:
            return (0, 0, "No device tokens")
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data,
                tokens=tokens
            )
            response = messaging.send_each_for_multicast(message)
            
            return (response.success_count, response.failure_count, None)
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"FCM send error: {error_msg}")
            return (0, len(tokens), error_msg)
    
    @classmethod
    async def send_notification(
        cls, 
        db: AsyncSession, 
        notification: Notification
    ) -> bool:
        """
        Send a single notification.
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Get device tokens for user
            tokens = await cls.get_device_tokens_for_user(db, notification.user_id)
            
            if not tokens:
                notification.status = NotificationStatus.FAILED
                notification.error_message = "No device tokens registered for user"
                notification.sent_at = datetime.now(timezone.utc)
                await db.commit()
                return False
            
            # Get task for message formatting
            task = await cls.get_task(db, notification.task_id)
            if not task:
                notification.status = NotificationStatus.FAILED
                notification.error_message = f"Task {notification.task_id} not found"
                notification.sent_at = datetime.now(timezone.utc)
                await db.commit()
                return False
            
            # Generate message from template using helper
            title, body = format_notification(notification.type, task)
            
            # Send via FCM
            data = {"notification_id": str(notification.id)}
            success, failures, error = cls._send_fcm_message(tokens, title, body, data=data)
            
            if success > 0:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)
                logger.info(f"Notification {notification.id} sent successfully to {success} devices")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = error or f"Failed to send to {failures} devices"
                notification.sent_at = datetime.now(timezone.utc)
                logger.error(f"Notification {notification.id} failed: {notification.error_message}")
            
            await db.commit()
            return notification.status == NotificationStatus.SENT
            
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            notification.status = NotificationStatus.FAILED
            notification.error_message = error_msg
            notification.sent_at = datetime.now(timezone.utc)
            await db.commit()
            logger.error(f"Error sending notification {notification.id}: {error_msg}")
            return False
    
    @classmethod
    async def send_all_pending(cls, db: AsyncSession) -> dict:
        """
        Process and send all pending notifications.
        Respects quiet hours.
        
        Returns:
            Dictionary with send statistics
        """
        # Initialize FCM if needed
        cls._initialize_fcm()
        
        # Check quiet hours
        if cls.is_quiet_hours():
            logger.info("Within quiet hours, skipping notification send")
            return {"sent": 0, "failed": 0, "skipped_quiet_hours": True}
        
        notifications = await cls.get_pending_notifications(db)
        
        sent = 0
        failed = 0
        
        for notification in notifications:
            success = await cls.send_notification(db, notification)
            if success:
                sent += 1
            else:
                failed += 1
        
        logger.info(f"Notification send complete: {sent} sent, {failed} failed")
        
        return {
            "sent": sent,
            "failed": failed,
            "skipped_quiet_hours": False
        }
