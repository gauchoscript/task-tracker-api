import boto3
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError
from app.core.config import settings
from app.schemas.auth import AuthRequest, TokenResponse

class AuthService:
    @staticmethod
    async def signin(signin_data: AuthRequest) -> TokenResponse:
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
                
            return TokenResponse(
                access_token=auth_result["AccessToken"],
                token_type=auth_result["TokenType"]
            )
            
        except ClientError as e:
            print(e)
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
    async def signup(signup_data: AuthRequest) -> bool:
        """
        Sign-up a new user using Amazon Cognito.
        """
        client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
        
        try:
            secret_hash = AuthService._calculate_secret_hash(
                signup_data.email, 
                settings.COGNITO_APP_CLIENT_ID, 
                settings.COGNITO_CLIENT_SECRET
            )
            
            client.sign_up(
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
            return True
            
        except ClientError as e:
            print(e)
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
