from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


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


class StudyMaterialResponse(BaseModel):
    """Schema for study material response"""
    id: UUID
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    title: str
    description: Optional[str]
    file_url: str
    file_type: str
    file_size: Optional[int]
    upload_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeacherStatisticsResponse(BaseModel):
    """Schema for teacher statistics"""
    teacher_id: UUID
    total_classes: int
    total_students: int

