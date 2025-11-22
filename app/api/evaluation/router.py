from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
import httpx
import logging
from app.api.evaluation.schemas import (
    AnswerEvaluationItem,
    AnswerEvaluationResponse,
    SingleAnswerEvaluation
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
    evaluations: List[AnswerEvaluationItem] = Body(..., description="Array of answer evaluations to process")
):
    """
    Evaluate multiple student answers against correct answers.
    
    Request body (array of JSON objects):
    [
        {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital of France.",
            "user's answer": "The capital is Paris"
        },
        {
            "question": "Who wrote Romeo and Juliet?",
            "answer": "William Shakespeare wrote Romeo and Juliet.",
            "user's answer": "Shakespeare"
        }
    ]
    
    The backend calls the AI service to evaluate all answers and returns scores and feedback for each.
    """
    try:
        # Validate request
        if not evaluations or len(evaluations) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one evaluation item is required in the array"
            )
        
        # Call AI service to evaluate multiple answers
        ai_service_url = settings.AI_SERVICE_URL
        webhook_url = f"{ai_service_url}/api/evaluate-answers"
        
        # Prepare payload - convert to format expected by AI service
        evaluations_payload = []
        for eval_item in evaluations:
            if not eval_item.question or not eval_item.answer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each evaluation must have both 'question' and 'answer' fields"
                )
            evaluations_payload.append({
                "question": eval_item.question,
                "answer": eval_item.answer,
                "student_answer": eval_item.user_answer
            })
        
        payload = {
            "evaluations": evaluations_payload
        }
        
        logger.info(f"📞 Calling AI service for answer evaluation - Processing {len(evaluations_payload)} answers")
        
        async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minute timeout for multiple evaluations
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                # The AI service returns results in a different format
                results_data = result.get("results", {})
                evaluations_result = results_data.get("evaluations", [])
                
                # Convert to our response format
                evaluation_results = []
                total_score = 0.0
                
                for eval_result in evaluations_result:
                    evaluation = eval_result.get("evaluation", {})
                    score = evaluation.get("score", 0.0)
                    total_score += score
                    
                    # Extract feedback from evaluation
                    feedback = evaluation.get("feedback", "")
                    
                    evaluation_results.append(
                        SingleAnswerEvaluation(
                            question=eval_result.get("question", ""),
                            score=score,
                            feedback=feedback,
                            evaluation=evaluation
                        )
                    )
                
                average_score = total_score / len(evaluation_results) if evaluation_results else 0.0
                
                logger.info(f"✅ Successfully evaluated {len(evaluation_results)} answers - Average Score: {average_score:.2f}/10")
                
                return AnswerEvaluationResponse(
                    success=True,
                    total_evaluations=len(evaluation_results),
                    evaluations=evaluation_results,
                    average_score=round(average_score, 2),
                    timestamp=result.get("timestamp")
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ AI service returned error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to evaluate answers: {error_msg}"
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
        logger.error(f"❌ Error evaluating answers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating answers: {str(e)}"
        )

