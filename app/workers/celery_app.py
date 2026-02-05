"""
Celery application configuration.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tasflou",
    broker=settings.get_redis_url(),
    backend=settings.get_redis_url(),
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute hard limit
    task_soft_time_limit=240,  # 4 minute soft limit
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "generate-notifications": {
        "task": "app.workers.tasks.generate_notifications_task",
        "schedule": 43200.0,  # Every 12 hours (in seconds)
    },
    "send-notifications": {
        "task": "app.workers.tasks.send_notifications_task",
        "schedule": 3600.0,  # Every hour (in seconds)
    },
}
