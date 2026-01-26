from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.models.notification import DeviceToken
from app.schemas.notification import DeviceTokenCreate
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

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
