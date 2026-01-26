from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class DeviceTokenCreate(BaseModel):
    token: str
    platform: str

class DeviceTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    token: str
    platform: str
    created_at: datetime
