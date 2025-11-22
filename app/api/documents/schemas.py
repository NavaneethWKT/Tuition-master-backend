from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class Base64UploadRequest(BaseModel):
    fileUrl: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Original filename with extension (e.g., document.pdf)")
    folder: Optional[str] = Field(None, description="Supabase Storage folder path (default: tuition_master/documents)")
    resource_type: str = Field("auto", description="Resource type (deprecated, kept for compatibility)")
    
    # Study Material fields
    class_id: UUID = Field(..., description="Class ID for the study material")
    subject_id: UUID = Field(..., description="Subject ID for the study material")
    teacher_id: UUID = Field(..., description="Teacher ID who uploaded the material")
    title: str = Field(..., description="Title of the study material")
    description: Optional[str] = Field(None, description="Description of the study material")
    
    model_config = ConfigDict(populate_by_name=True)


class DocumentUploadResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    public_id: Optional[str] = None
    format: Optional[str] = None
    resource_type: Optional[str] = None
    bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[str] = None
    error: Optional[str] = None
    study_material_id: Optional[UUID] = None


class DocumentDeleteResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class DocumentURLResponse(BaseModel):
    url: str
    public_id: str

