import boto3
import logging
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.schemas.auth import AuthRequest, TokenResponse, RefreshRequest
from app.models.user import User

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    async def signin(signin_data: AuthRequest, db: AsyncSession) -> TokenResponse:
        """
        Sign-in using Amazon Cognito.
        """
        client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
        
        try:
            secret_hash = AuthService._calculate_secret_hash(
                signin_data.email, 
                settings.COGNITO_APP_CLIENT_ID, 
                settings.COGNITO_CLIENT_SECRET
            )
            
            response = client.initiate_auth(
                ClientId=settings.COGNITO_APP_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": signin_data.email,
                    "PASSWORD": signin_data.password,
                    "SECRET_HASH": secret_hash,
                },
            )
            
            auth_result = response.get("AuthenticationResult")
            if not auth_result:
                return None
            
            # Check if user exists in local DB
            result = await db.execute(select(User).where(User.email == signin_data.email))
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User {signin_data.email} exists in Cognito but not in local DB")
                return None
                
            return TokenResponse(
                access_token=auth_result.get("AccessToken"),
                token_type=auth_result.get("TokenType"),
                refresh_token=auth_result.get("RefreshToken"),
                expires_in=auth_result.get("ExpiresIn")
            )
            
        except ClientError as e:
            logger.error(f"Cognito signin error: {e}")
            error_code = e.response["Error"]["Code"]
            if error_code in [
                "NotAuthorizedException", 
                "UserNotFoundException",
                "UserNotConfirmedException",
                "PasswordResetRequiredException"
            ]:
                return None
            raise e

    @staticmethod
    async def refresh_token(refresh_data: RefreshRequest) -> TokenResponse:
        """
        Refresh tokens using REFRESH_TOKEN_AUTH flow.
        """
        client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
        
        try:
            secret_hash = AuthService._calculate_secret_hash(
                refresh_data.email,
                settings.COGNITO_APP_CLIENT_ID,
                settings.COGNITO_CLIENT_SECRET
            )
            
            response = client.initiate_auth(
                ClientId=settings.COGNITO_APP_CLIENT_ID,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_data.refresh_token,
                    "SECRET_HASH": secret_hash,
                },
            )
            
            auth_result = response.get("AuthenticationResult")
            if not auth_result:
                return None
                
            return TokenResponse(
                access_token=auth_result.get("AccessToken"),
                token_type=auth_result.get("TokenType"),
                refresh_token=auth_result.get("RefreshToken"),
                expires_in=auth_result.get("ExpiresIn")
            )
            
        except ClientError as e:
            logger.error(f"Cognito refresh error: {e}")
            raise e

    @staticmethod
    async def signup(signup_data: AuthRequest, db: AsyncSession) -> bool:
        """
        Sign-up a new user using Amazon Cognito and save to local DB.
        """
        client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
        
        try:
            secret_hash = AuthService._calculate_secret_hash(
                signup_data.email, 
                settings.COGNITO_APP_CLIENT_ID, 
                settings.COGNITO_CLIENT_SECRET
            )
            
            response = client.sign_up(
                ClientId=settings.COGNITO_APP_CLIENT_ID,
                Username=signup_data.email,
                Password=signup_data.password,
                SecretHash=secret_hash,
                UserAttributes=[
                    {
                        "Name": "email",
                        "Value": signup_data.email
                    },
                ],
            )
            
            # Save to local DB
            external_id = response.get("UserSub")
            if not external_id:
                # Cognito might not return UserSub if it's already pre-confirmed or other cases
                # but for sign_up it usually does.
                return False
                
            new_user = User(
                email=signup_data.email,
                external_id=external_id
            )
            db.add(new_user)
            await db.commit()
            
            return True
            
        except ClientError as e:
            logger.error(f"Cognito signup error: {e}")
            return False
    @staticmethod
    def _calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
        """
        Calculate the SECRET_HASH for Cognito.
        Formula: Base64(HMAC_SHA256(client_secret, username + client_id))
        """
        message = username + client_id
        dig = hmac.new(
            client_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
