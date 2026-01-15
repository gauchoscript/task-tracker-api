import os

# Set dummy environment variables for tests
os.environ["COGNITO_USER_POOL_ID"] = "dummy_pool_id"
os.environ["COGNITO_APP_CLIENT_ID"] = "dummy_client_id"
os.environ["COGNITO_CLIENT_SECRET"] = "dummy_client_secret"
os.environ["COGNITO_REGION"] = "us-east-1"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres"
os.environ["POSTGRES_DB"] = "postgres"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"

import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import AuthService
from app.schemas.auth import AuthRequest
from app.models.user import User

@pytest.mark.asyncio
async def test_user_signup_syncs_to_db():
    """
    Test that a successful Cognito signup triggers a user creation in the local database.
    """
    email = "newuser@example.com"
    password = "Password123!"
    external_id = "550e8400-e29b-41d4-a716-446655440000"
    
    signup_data = AuthRequest(email=email, password=password)
    mock_db = MagicMock(spec=AsyncSession)
    
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        # Cognito return UserSub on successful sign_up
        mock_client.sign_up.return_value = {"UserSub": external_id}
        
        # Action
        success = await AuthService.signup(signup_data, mock_db)
        
        # Assertions
        assert success is True
        
        # Verify Cognito was called
        mock_client.sign_up.assert_called_once()
        
        # Verify DB interactions
        mock_db.add.assert_called_once()
        
        # Check that the added object is a User with correct attributes
        added_user = mock_db.add.call_args[0][0]
        assert isinstance(added_user, User)
        assert added_user.email == email
        assert added_user.external_id == external_id
        
        mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_user_signup_failure_no_db_sync():
    """
    Test that if Cognito signup fails, no user is created in the local database.
    """
    signup_data = AuthRequest(email="fail@example.com", password="password")
    mock_db = MagicMock(spec=AsyncSession)
    
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.sign_up.side_effect = ClientError(
            {"Error": {"Code": "InternalErrorException", "Message": "Cognito Error"}},
            "SignUp"
        )
        
        # Action
        success = await AuthService.signup(signup_data, mock_db)
        
        # Assertions
        assert success is False
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
