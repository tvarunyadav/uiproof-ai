from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User registration email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User login email address")
    password: str = Field(..., description="User login password")


class UserResponse(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(..., description="User account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token authorization type")


class LogoutResponse(BaseModel):
    message: str = Field(default="Logged out successfully.", description="Stateless logout notification")
