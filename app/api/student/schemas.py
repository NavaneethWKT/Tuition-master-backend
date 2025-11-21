from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional
from uuid import UUID


class StudentCreate(BaseModel):
    """Schema for creating a student"""
    school_id: UUID
    class_id: Optional[UUID] = None
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    date_of_birth: str  # Date in YYYY-MM-DD format
    roll_number: Optional[str] = None
    admission_date: str  # Date in YYYY-MM-DD format


class StudentResponse(BaseModel):
    """Schema for student response"""
    id: UUID
    school_id: UUID
    class_id: Optional[UUID]
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    date_of_birth: date
    roll_number: Optional[str]
    admission_date: date
    created_at: datetime
    
    class Config:
        from_attributes = True

