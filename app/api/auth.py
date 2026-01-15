from fastapi import APIRouter, HTTPException, status, Depends
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import AuthRequest, TokenResponse
from app.services.auth import AuthService
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signin", response_model=TokenResponse)
async def signin(signin_data: AuthRequest):
    """
    Sign-in endpoint calling the service layer.
    """
    try:
        result = await AuthService.signin(signin_data)
        if result:
            return result
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except ClientError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(signup_data: AuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Sign-up endpoint calling the service layer.
    """
    try:
        success = await AuthService.signup(signup_data, db)
        if success:
            return {"message": "User created successfully. Please check your email for confirmation."}
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user",
        )
    except ClientError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )
