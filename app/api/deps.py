import json
import urllib.request
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.PROJECT_NAME}/auth/signin" # Placeholder, adjust if needed
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        # 1. Get Cognito JWKS (JSON Web Key Set)
        # In a production app, you might want to cache this.
        region = settings.COGNITO_REGION
        user_pool_id = settings.COGNITO_USER_POOL_ID
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        
        with urllib.request.urlopen(jwks_url) as response:
            jwks = json.loads(response.read().decode())

        # 2. Decode and verify the token
        # For simplicity in this step, we'll use jose.jwt.decode
        # It handles signature verification if we provide the keys.
        # But Cognito uses multiple keys, so we need to find the right one.
        
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        key = None
        for k in jwks.get("keys", []):
            if k["kid"] == kid:
                key = k
                break
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header",
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        )
        
        external_id = payload.get("sub")
        if not external_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
            
        # 3. Look up user in local DB
        query = select(User).where(User.external_id == external_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        return user

    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
