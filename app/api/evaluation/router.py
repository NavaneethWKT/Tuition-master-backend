from fastapi import APIRouter, HTTPException, status, Body, Depends
import httpx
import logging
from app.api.evaluation.schemas import (
    AnswerEvaluationRequest,
    AnswerEvaluationResponse
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/evaluation",
    tags=["Evaluation"]
)


@router.post(
    "/answer",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_200_OK
)
async def evaluate_answer(
    request: AnswerEvaluationRequest = Body(..., description="Answer evaluation request")
):
    """
    Evaluate a student's answer against the correct answer.
    
    Request body:
    {
        "question": "What is the capital of France?",
        "answer": "Paris is the capital of France.",
        "user's answer": "The capital is Paris"
    }
    
    The backend calls the AI service to evaluate the answer and returns the score and feedback.
    """
    try:
        # Validate request
        if not request.question or not request.answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'question' and 'answer' are required"
            )
        
        # Call AI service to evaluate answer
        ai_service_url = settings.AI_SERVICE_URL
        webhook_url = f"{ai_service_url}/api/evaluate-answer"
        
        # Prepare payload - map "user_answer" to "student_answer" for AI service
        payload = {
            "question": request.question,
            "answer": request.answer,
            "student_answer": request.user_answer
        }
        
        logger.info(f"📞 Calling AI service for answer evaluation - Question: {request.question[:50]}...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # 1 minute timeout
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                evaluation = result.get("evaluation", {})
                score = evaluation.get("score", 0.0)
                feedback = evaluation.get("feedback", "")
                
                logger.info(f"✅ Successfully evaluated answer - Score: {score}/10")
                
                return AnswerEvaluationResponse(
                    success=True,
                    question=request.question,
                    score=score,
                    feedback=feedback,
                    evaluation=evaluation,
                    timestamp=result.get("timestamp")
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ AI service returned error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to evaluate answer: {error_msg}"
                )
    
    except httpx.TimeoutException:
        logger.error("❌ Timeout calling AI service for answer evaluation")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to AI service timed out. Please try again."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error calling AI service: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service returned error: {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error evaluating answer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating answer: {str(e)}"
        )

