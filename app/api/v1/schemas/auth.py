from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime


#  Register 
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


#  Login 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


#  Token response 
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


#  User response (safe, no password) 
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
