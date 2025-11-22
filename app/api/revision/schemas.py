from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class RevisionPointersRequest(BaseModel):
    """Request schema for generating revision pointers"""
    study_material_id: Optional[UUID] = Field(None, description="Study Material ID to generate revision pointers for")
    subject: Optional[str] = Field(None, description="Subject name (e.g., 'History')")
    class_level: Optional[str] = Field(None, description="Class level (e.g., '10')")
    chapter: Optional[str] = Field(None, description="Chapter name (e.g., 'A Brief History of India')")


class RevisionPointersResponse(BaseModel):
    """Response schema for revision pointers"""
    success: bool
    subject: Optional[str] = None
    class_level: Optional[str] = None
    chapter: Optional[str] = None
    pointers: List[str] = []
    total_pointers: int = 0
    error: Optional[str] = None
    timestamp: Optional[str] = None


class RevisionCreate(BaseModel):
    """Schema for creating a revision"""
    student_id: UUID
    subject: str
    class_level: str
    chapter: str
    pointers: List[str]  # Array of strings
    total_pointers: int


class RevisionResponse(BaseModel):
    """Schema for revision response"""
    id: UUID
    student_id: UUID
    subject: str
    class_level: str
    chapter: str
    pointers: List[str]
    total_pointers: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

