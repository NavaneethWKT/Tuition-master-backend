from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class ParentLogin(BaseModel):
    """Schema for parent login request"""
    phone: str
    password: str


class ParentCreate(BaseModel):
    """Schema for creating a parent"""
    student_id: UUID
    full_name: str
    email: EmailStr
    phone: str
    password: str


class ParentResponse(BaseModel):
    """Schema for parent response after login"""
    id: UUID
    student_id: UUID
    full_name: str
    email: str
    phone: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ParentLoginResponse(BaseModel):
    """Schema for successful login response"""
    message: str
    parent: ParentResponse
    access_token: Optional[str] = None  # For future JWT implementation

