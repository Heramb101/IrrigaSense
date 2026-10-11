from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Unique username (alphanumeric and underscores)")
    password: str = Field(..., min_length=8, max_length=128, description="Account password (min 8 characters)")
    name: Optional[str] = Field(default=None, max_length=100, description="Farmer display name")

class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Account username")
    password: str = Field(..., description="Account password")

class UserRead(BaseModel):
    id: int
    username: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuthResponse(BaseModel):
    user: UserRead
    message: str = "Authenticated successfully"
    csrf_token: str

class MessageResponse(BaseModel):
    message: str
