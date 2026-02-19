"""
Notification message templates for each notification type.
Templates use Python string formatting with task/user properties.
"""
from datetime import datetime, timezone
from app.models.notification import NotificationType


NOTIFICATION_TEMPLATES = {
    NotificationType.DUE_DATE_APPROACHING: {
        "title": "Task due soon",
        "body": "'{task_title}' is due on {due_date}"
    },
    NotificationType.STALE_TASK: {
        "title": "Task needs attention",
        "body": "'{task_title}' has been in {status} for {days} days"
    }
}


def get_notification_message(
    notification_type: NotificationType,
    task_title: str,
    **kwargs
) -> tuple[str, str]:
    """
    Generate notification title and body from template.
    
    Args:
        notification_type: The type of notification
        task_title: The task's title
        **kwargs: Additional formatting parameters (due_date, status, days, etc.)
    
    Returns:
        Tuple of (title, body)
    """
    template = NOTIFICATION_TEMPLATES[notification_type]
    
    format_args = {"task_title": task_title, **kwargs}
    
    title = template["title"]
    body = template["body"].format(**format_args)
    
    return title, body


def format_notification(
    notification_type: NotificationType,
    task
) -> tuple[str, str]:
    """
    Higher-level helper to generate notification title and body from a Task object.
    Handles extraction of common fields (due_date, status, days).
    """
    format_kwargs = {
        "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A",
        "status": task.status.value if task.status else "unknown",
    }
    
    # Add specific context for stale tasks if available
    if notification_type == NotificationType.STALE_TASK and hasattr(task, 'status_changed_at') and task.status_changed_at:
        format_kwargs["days"] = (datetime.now(timezone.utc) - task.status_changed_at).days
    
    return get_notification_message(
        notification_type,
        task.title,
        **format_kwargs
    )
