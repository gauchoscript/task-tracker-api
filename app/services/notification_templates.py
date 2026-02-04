"""
Notification message templates for each notification type.
Templates use Python string formatting with task/user properties.
"""
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
