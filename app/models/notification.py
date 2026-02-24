from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import enum
import uuid


class DeviceToken(Base):
    __tablename__ = "device_token"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    platform = Column(String, nullable=False)  # web, android, ios
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)


class NotificationType(str, enum.Enum):
    DUE_DATE_APPROACHING = "due_date_approaching"
    STALE_TASK = "stale_task"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ReadSource(str, enum.Enum):
    WEB_PUSH = "web_push"
    WEB_CLIENT = "web_client"


class Notification(Base):
    __tablename__ = "notification"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("task.id"), nullable=True)
    type = Column(Enum(NotificationType, values_callable=lambda obj: [e.value for e in obj], name="notificationtype"), nullable=False)
    status = Column(Enum(NotificationStatus, values_callable=lambda obj: [e.value for e in obj], name="notificationstatus"), default=NotificationStatus.PENDING)
    
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    read_at = Column(DateTime(timezone=True), nullable=True)
    read_source = Column(Enum(ReadSource, values_callable=lambda obj: [e.value for e in obj], name="readsource"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
