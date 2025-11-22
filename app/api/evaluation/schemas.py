from pydantic import BaseModel, Field, ConfigDict


class AnswerEvaluationRequest(BaseModel):
    """Request schema for evaluating a student's answer"""
    model_config = ConfigDict(populate_by_name=True)
    
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The correct answer")
    user_answer: str = Field(..., alias="user's answer", description="The student's/user's answer to evaluate")


class AnswerEvaluationResponse(BaseModel):
    """Response schema for answer evaluation"""
    success: bool
    question: str
    score: float = Field(..., description="Score out of 10")
    feedback: str = Field(..., description="Detailed feedback on the answer")
    evaluation: dict = Field(..., description="Full evaluation details from AI service")
    timestamp: str = None
    error: str = None

