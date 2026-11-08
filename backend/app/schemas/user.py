from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class UserBase(BaseModel):
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password (min 8 chars)")


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
