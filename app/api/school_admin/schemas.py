from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class SchoolCreate(BaseModel):
    """Schema for creating a school"""
    name: str
    address: str
    contact_phone: str
    contact_email: EmailStr
    establishment_year: Optional[int] = None
    board_affiliation: Optional[str] = None  # CBSE, ICSE, State Board, IGCSE, IB, Other
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    principal_name: Optional[str] = None
    principal_email: Optional[EmailStr] = None
    principal_phone: Optional[str] = None
    admin_name: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    admin_phone: Optional[str] = None
    password: str  # Will be hashed before storing


class SchoolResponse(BaseModel):
    """Schema for school response"""
    id: UUID
    name: str
    address: str
    contact_phone: str
    contact_email: str
    establishment_year: Optional[int]
    board_affiliation: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    principal_name: Optional[str]
    principal_email: Optional[str]
    principal_phone: Optional[str]
    admin_name: Optional[str]
    admin_email: Optional[str]
    admin_phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeacherCreate(BaseModel):
    """Schema for creating a teacher"""
    school_id: UUID
    full_name: str
    email: Optional[EmailStr] = None
    phone: str
    password: str
    subjects: list[str]  # Array of subject names
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    joining_date: str  # Date in YYYY-MM-DD format


class TeacherResponse(BaseModel):
    """Schema for teacher response"""
    id: UUID
    school_id: UUID
    full_name: str
    email: Optional[str]
    phone: str
    subjects: list[str]
    qualification: Optional[str]
    experience_years: Optional[int]
    joining_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class SchoolDetailsResponse(BaseModel):
    """Schema for school details with statistics"""
    id: UUID
    name: str
    address: str
    contact_phone: str
    contact_email: str
    establishment_year: Optional[int]
    board_affiliation: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    principal_name: Optional[str]
    principal_email: Optional[str]
    principal_phone: Optional[str]
    admin_name: Optional[str]
    admin_email: Optional[str]
    admin_phone: Optional[str]
    created_at: datetime
    total_students: int
    total_classes: int
    total_teachers: int
    
    class Config:
        from_attributes = True


class ClassResponse(BaseModel):
    """Schema for class response"""
    id: UUID
    school_id: UUID
    grade: int
    section: str
    class_teacher_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

