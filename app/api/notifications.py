from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.notification import DeviceTokenCreate, DeviceTokenResponse, NotificationResponse, MarkReadRequest
from app.services.notification import NotificationService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/devices", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_in: DeviceTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register or update a device token for the authenticated user.
    """
    return await NotificationService.register_device(db, device_in, current_user.id)

@router.delete("/devices/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unregister a device token for the authenticated user.
    """
    success = await NotificationService.unregister_device(db, token, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device token not found for this user"
        )
    return None

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List sent notifications for the authenticated user with pagination, unread first.
    """
    return await NotificationService.get_notifications_for_user(db, current_user.id, skip=skip, limit=limit)

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    read_in: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read for the authenticated user.
    """
    notification = await NotificationService.mark_notification_read(
        db, notification_id, current_user.id, read_in.read_source
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification
