from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.notification import NotificationType, NotificationStatus, ReadSource

class DeviceTokenCreate(BaseModel):
    token: str
    platform: str

class DeviceTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    token: str
    platform: str
    created_at: datetime

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    task_id: Optional[UUID] = None
    title: str = ""
    message: str = ""
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

class MarkReadRequest(BaseModel):
    read_source: ReadSource

class NotificationPaginated(BaseModel):
    items: List[NotificationResponse]
    total: int
    skip: int
    limit: int
