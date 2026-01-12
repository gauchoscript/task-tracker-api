from fastapi import APIRouter, HTTPException, status
from botocore.exceptions import ClientError
from app.schemas.auth import SignInRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signin", response_model=TokenResponse)
async def signin(signin_data: SignInRequest):
    """
    Boilerplate sign-in endpoint calling the service layer.
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
