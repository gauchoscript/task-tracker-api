from pydantic import BaseModel, EmailStr

from typing import Optional

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

class RefreshRequest(BaseModel):
    email: EmailStr
    refresh_token: str
