from fastapi import APIRouter, HTTPException, status, Body, Depends, Query, Path
from typing import Optional, List
import httpx
import logging
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.revision.schemas import (
    RevisionPointersRequest,
    RevisionPointersResponse,
    RevisionCreate,
    RevisionResponse
)
from app.database import get_db
from app import models
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/revision",
    tags=["Revision"]
)


@router.post(
    "/pointers",
    response_model=RevisionPointersResponse,
    status_code=status.HTTP_200_OK
)
async def generate_revision_pointers(
    request: RevisionPointersRequest = Body(..., description="Request to generate revision pointers"),
    db: Session = Depends(get_db)
):
    """
    Generate revision pointers for a study material.
    
    You can provide either:
    - study_material_id: The UUID of the study material (will fetch subject, class, and title from DB)
    - OR manually provide: subject, class_level, and chapter
    
    The backend calls the AI service to generate revision pointers and returns the JSON response.
    """
    try:
        subject = request.subject
        class_level = request.class_level
        chapter = request.chapter
        
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
        
        # Call AI service to generate revision pointers
        ai_service_url = settings.AI_SERVICE_URL
        webhook_url = f"{ai_service_url}/api/revision-pointers"
        
        logger.info(f"📞 Calling AI service for revision pointers - Subject: {subject}, Class: {class_level}, Chapter: {chapter}")
        logger.info(f"⚠️ Note: AI service currently uses hardcoded values. Parameters provided: Subject={subject}, Class={class_level}, Chapter={chapter}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minute timeout
            response = await client.post(webhook_url)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                logger.info(f"✅ Successfully generated {result.get('total_pointers', 0)} revision pointers")
                return RevisionPointersResponse(
                    success=True,
                    subject=result.get("subject"),
                    class_level=result.get("class_level"),
                    chapter=result.get("chapter"),
                    pointers=result.get("pointers", []),
                    total_pointers=result.get("total_pointers", 0),
                    timestamp=result.get("timestamp")
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ AI service returned error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate revision pointers: {error_msg}"
                )
    
    except httpx.TimeoutException:
        logger.error("❌ Timeout calling AI service for revision pointers")
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
        logger.error(f"❌ Error generating revision pointers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating revision pointers: {str(e)}"
        )


@router.get(
    "/pointers",
    response_model=RevisionPointersResponse,
    status_code=status.HTTP_200_OK
)
async def get_revision_pointers(
    study_material_id: Optional[str] = Query(None, description="Study Material ID (UUID)"),
    subject: Optional[str] = Query(None, description="Subject name"),
    class_level: Optional[str] = Query(None, description="Class level"),
    chapter: Optional[str] = Query(None, description="Chapter name"),
    db: Session = Depends(get_db)
):
    """
    Generate revision pointers (GET endpoint).
    
    You can provide either:
    - study_material_id: The UUID of the study material
    - OR manually provide: subject, class_level, and chapter as query parameters
    """
    request = RevisionPointersRequest(
        study_material_id=study_material_id,
        subject=subject,
        class_level=class_level,
        chapter=chapter
    )
    return await generate_revision_pointers(request=request, db=db)


@router.post(
    "/revisions",
    response_model=RevisionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_revision(
    revision_data: RevisionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new revision for a student.
    
    Requires:
    - student_id: UUID of the student
    - subject: Subject name (string)
    - class_level: Class level (string)
    - chapter: Chapter name (string)
    - pointers: Array of strings (revision pointers)
    - total_pointers: Total number of pointers (integer)
    """
    logger.info(f"📝 Creating revision for student_id: {revision_data.student_id}")
    
    # Verify student exists
    student = db.query(models.Student).filter(models.Student.id == revision_data.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student not found with ID: {revision_data.student_id}"
        )
    
    # Validate total_pointers matches the length of pointers array
    if revision_data.total_pointers != len(revision_data.pointers):
        logger.warning(f"⚠️ total_pointers ({revision_data.total_pointers}) doesn't match pointers array length ({len(revision_data.pointers)}). Using array length.")
        revision_data.total_pointers = len(revision_data.pointers)
    
    # Create revision record
    revision = models.Revision(
        student_id=revision_data.student_id,
        subject=revision_data.subject,
        class_level=revision_data.class_level,
        chapter=revision_data.chapter,
        pointers=revision_data.pointers,
        total_pointers=revision_data.total_pointers
    )
    
    db.add(revision)
    db.commit()
    db.refresh(revision)
    
    logger.info(f"✅ Revision created successfully - ID: {revision.id}, Student: {revision_data.student_id}, Subject: {revision_data.subject}, Chapter: {revision_data.chapter}")
    
    return revision


@router.get(
    "/students/{student_id}/revisions",
    response_model=List[RevisionResponse],
    status_code=status.HTTP_200_OK
)
async def get_student_revisions(
    student_id: UUID = Path(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all revisions for a particular student.
    
    Returns a list of all revisions associated with the specified student.
    """
    logger.info(f"📖 Retrieving revisions for student_id: {student_id}")
    
    # Verify student exists
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student not found with ID: {student_id}"
        )
    
    # Get all revisions for the student
    revisions = db.query(models.Revision).filter(
        models.Revision.student_id == student_id
    ).order_by(models.Revision.created_at.desc()).all()
    
    logger.info(f"✅ Found {len(revisions)} revision(s) for student_id: {student_id}")
    
    return revisions

