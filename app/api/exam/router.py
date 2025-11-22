from fastapi import APIRouter, HTTPException, status, Body, Depends, Query
from typing import Optional
import httpx
import logging
from sqlalchemy.orm import Session
from app.api.exam.schemas import (
    ExamQuestionsRequest,
    ExamQuestionsResponse
)
from app.database import get_db
from app import models
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/exam",
    tags=["Exam"]
)


@router.post(
    "/questions",
    response_model=ExamQuestionsResponse,
    status_code=status.HTTP_200_OK
)
async def generate_exam_questions(
    request: ExamQuestionsRequest = Body(..., description="Request to generate exam questions"),
    db: Session = Depends(get_db)
):
    """
    Generate exam questions for a study material.
    
    You can provide either:
    - study_material_id: The UUID of the study material (will fetch subject, class, and title from DB)
    - OR manually provide: subject, class_level, and chapter
    
    The backend calls the AI service to generate exam questions and returns the JSON response.
    """
    try:
        subject = request.subject
        class_level = request.class_level
        chapter = request.chapter
        num_questions = request.num_questions or 10
        
        # If study_material_id is provided, fetch details from database
        if request.study_material_id:
            logger.info(f"🔍 Fetching study material details for ID: {request.study_material_id}")
            study_material = db.query(models.StudyMaterial).filter(
                models.StudyMaterial.id == request.study_material_id
            ).first()
            
            if not study_material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Study material not found with ID: {request.study_material_id}"
                )
            
            # Get subject and class details
            subject_obj = db.query(models.Subject).filter(
                models.Subject.id == study_material.subject_id
            ).first()
            
            class_obj = db.query(models.Class).filter(
                models.Class.id == study_material.class_id
            ).first()
            
            if not subject_obj or not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject or Class not found for the study material"
                )
            
            subject = subject_obj.name
            class_level = str(class_obj.grade)
            chapter = study_material.title
            
            logger.info(f"✅ Found study material - Subject: {subject}, Class: {class_level}, Chapter: {chapter}")
        
        # Validate required fields
        if not subject or not class_level or not chapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'study_material_id' must be provided, or 'subject', 'class_level', and 'chapter' must all be provided"
            )
        
        # Call AI service to generate exam questions
        ai_service_url = settings.AI_SERVICE_URL
        webhook_url = f"{ai_service_url}/api/exam-questions"
        
        # Prepare payload with study_material_id if available
        payload = {
            "subject": subject,
            "class_level": class_level,
            "chapter": chapter,
            "num_questions": num_questions
        }
        
        # If we have study_material_id from the request, include it
        if request.study_material_id:
            payload["study_material_id"] = str(request.study_material_id)
        
        logger.info(f"📞 Calling AI service for exam questions - study_material_id: {request.study_material_id}, Subject: {subject}, Class: {class_level}, Chapter: {chapter}, Num Questions: {num_questions}")
        
        async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minute timeout for question generation
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                logger.info(f"✅ Successfully generated {result.get('total_questions', 0)} exam questions")
                return ExamQuestionsResponse(
                    success=True,
                    subject=result.get("subject"),
                    class_level=result.get("class_level"),
                    chapter=result.get("chapter"),
                    total_questions=result.get("total_questions", 0),
                    questions=result.get("questions", []),
                    timestamp=result.get("timestamp")
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ AI service returned error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate exam questions: {error_msg}"
                )
    
    except httpx.TimeoutException:
        logger.error("❌ Timeout calling AI service for exam questions")
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
        logger.error(f"❌ Error generating exam questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating exam questions: {str(e)}"
        )


@router.get(
    "/questions",
    response_model=ExamQuestionsResponse,
    status_code=status.HTTP_200_OK
)
async def get_exam_questions(
    study_material_id: Optional[str] = Query(None, description="Study Material ID (UUID)"),
    subject: Optional[str] = Query(None, description="Subject name"),
    class_level: Optional[str] = Query(None, description="Class level"),
    chapter: Optional[str] = Query(None, description="Chapter name"),
    num_questions: Optional[int] = Query(10, description="Number of questions to generate"),
    db: Session = Depends(get_db)
):
    """
    Generate exam questions (GET endpoint).
    
    You can provide either:
    - study_material_id: The UUID of the study material
    - OR manually provide: subject, class_level, and chapter as query parameters
    """
    request = ExamQuestionsRequest(
        study_material_id=study_material_id,
        subject=subject,
        class_level=class_level,
        chapter=chapter,
        num_questions=num_questions
    )
    return await generate_exam_questions(request=request, db=db)

