from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID


class ExamQuestionsRequest(BaseModel):
    """Request schema for generating exam questions"""
    study_material_id: Optional[UUID] = Field(None, description="Study Material ID to generate exam questions for")
    subject: Optional[str] = Field(None, description="Subject name (e.g., 'History')")
    class_level: Optional[str] = Field(None, description="Class level (e.g., '10')")
    chapter: Optional[str] = Field(None, description="Chapter name (e.g., 'A Brief History of India')")
    num_questions: Optional[int] = Field(10, description="Number of questions to generate (default: 10)")


class ExamQuestionItem(BaseModel):
    """Individual exam question item"""
    question: str
    answer: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None


class ExamQuestionsResponse(BaseModel):
    """Response schema for exam questions"""
    success: bool
    subject: Optional[str] = None
    class_level: Optional[str] = None
    chapter: Optional[str] = None
    total_questions: int = 0
    questions: List[Dict] = []
    timestamp: Optional[str] = None
    error: Optional[str] = None

