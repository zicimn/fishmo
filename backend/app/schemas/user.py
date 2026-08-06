from pydantic import BaseModel,EmailStr,Field,field_validator
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str


class Account(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=6, max_length=20)
    email: EmailStr
    avatar: Optional[str] = None
    bio: Optional[str] = None


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=2, max_length=20)
    password: Optional[str] = Field(default=None, min_length=6, max_length=20)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None