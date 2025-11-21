from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    """Schema for login request - supports phone or email based on persona"""
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+91-9876554321",
                "password": "password123"
            }
        }


class ParentLoginResponse(BaseModel):
    """Schema for parent login response"""
    message: str
    persona: str = "parent"
    id: UUID
    student_id: UUID
    full_name: str
    email: str
    phone: str
    created_at: datetime
    access_token: Optional[str] = None


class StudentLoginResponse(BaseModel):
    """Schema for student login response"""
    message: str
    persona: str = "student"
    id: UUID
    school_id: UUID
    class_id: Optional[UUID]
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    roll_number: Optional[str]
    created_at: datetime
    access_token: Optional[str] = None


class TeacherLoginResponse(BaseModel):
    """Schema for teacher login response"""
    message: str
    persona: str = "teacher"
    id: UUID
    school_id: UUID
    full_name: str
    email: Optional[str]
    phone: str
    subjects: list[str]
    qualification: Optional[str]
    created_at: datetime
    access_token: Optional[str] = None


class SchoolLoginResponse(BaseModel):
    """Schema for school login response"""
    message: str
    persona: str = "school"
    id: UUID
    name: str
    contact_email: str
    contact_phone: str
    city: Optional[str]
    state: Optional[str]
    board_affiliation: Optional[str]
    created_at: datetime
    access_token: Optional[str] = None

