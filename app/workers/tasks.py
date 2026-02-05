"""
Celery tasks for notification processing.
"""
from app.workers.celery_app import celery_app
from app.core.database import async_session_maker
from app.services.notification_generator import NotificationGenerator
from app.services.notification_sender import NotificationSender
import asyncio
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.generate_notifications_task")
def generate_notifications_task():
    """
    Periodic task to generate notifications.
    Runs every 12 hours to detect tasks that need notifications.
    """
    logger.info("Starting notification generation task")
    
    async def _generate():
        async with async_session_maker() as db:
            try:
                result = await NotificationGenerator.generate_all(db)
                logger.info(f"Notification generation complete: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in notification generation: {e}")
                raise
    
    return run_async(_generate())


@celery_app.task(name="app.workers.tasks.send_notifications_task")
def send_notifications_task():
    """
    Periodic task to send pending notifications.
    Runs every hour, respects quiet hours.
    """
    logger.info("Starting notification send task")
    
    async def _send():
        async with async_session_maker() as db:
            try:
                result = await NotificationSender.send_all_pending(db)
                logger.info(f"Notification send complete: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in notification send: {e}")
                raise
    
    return run_async(_send())
