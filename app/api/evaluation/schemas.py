from pydantic import BaseModel, Field, ConfigDict
from typing import List


class AnswerEvaluationItem(BaseModel):
    """Single answer evaluation item"""
    model_config = ConfigDict(populate_by_name=True)
    
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The correct answer")
    user_answer: str = Field(..., alias="user's answer", description="The student's/user's answer to evaluate")


class AnswerEvaluationRequest(BaseModel):
    """Request schema for evaluating multiple student answers"""
    evaluations: List[AnswerEvaluationItem] = Field(..., description="Array of answer evaluations to process")


class SingleAnswerEvaluation(BaseModel):
    """Single answer evaluation result"""
    question: str
    score: float = Field(..., description="Score out of 10")
    feedback: str = Field(..., description="Detailed feedback on the answer")
    evaluation: dict = Field(..., description="Full evaluation details from AI service")


class AnswerEvaluationResponse(BaseModel):
    """Response schema for answer evaluation"""
    success: bool
    total_evaluations: int = Field(..., description="Total number of evaluations processed")
    evaluations: List[SingleAnswerEvaluation] = Field(..., description="List of evaluation results")
    average_score: float = Field(..., description="Average score across all evaluations")
    timestamp: str = None
    error: str = None

