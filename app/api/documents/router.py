from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, Query, Body, Depends, BackgroundTasks
from typing import Optional
import tempfile
import os
import base64
import httpx
import logging
from sqlalchemy.orm import Session
from app.api.documents.schemas import (
    Base64UploadRequest,
    DocumentUploadResponse,
    DocumentDeleteResponse,
    DocumentURLResponse
)
from app.utils.cloudinary import (
    upload_file_from_bytes,
    delete_file,
    get_file_url
)
from app.database import get_db
from app import models
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


async def create_embeddings_async(
    file_url: str,
    document_id: str,
    subject_name: str,
    class_level: str,
    title: str,
    filename: str
):
    """
    Asynchronously call AI service to create embeddings for a study material.
    This runs in the background and doesn't block the API response.
    """
    logger.info(f"[EMBEDDING] Starting embedding creation process for document_id: {document_id}")
    logger.info(f"[EMBEDDING] Details - Subject: {subject_name}, Class: {class_level}, Title: {title}, Filename: {filename}")
    
    try:
        ai_service_url = settings.AI_SERVICE_URL
        webhook_url = f"{ai_service_url}/api/create-embeddings"
        
        payload = {
            "file_url": file_url,
            "document_id": document_id,
            "subject": subject_name,
            "class_level": str(class_level),
            "title": title,
            "filename": filename
        }
        
        logger.info(f"[EMBEDDING] Calling AI service webhook: {webhook_url}")
        logger.debug(f"[EMBEDDING] Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for large files
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                logger.info(f"[EMBEDDING] ✅ SUCCESS: Embeddings created successfully for document_id: {document_id}")
                logger.info(f"[EMBEDDING] Response: {result.get('message', 'N/A')}, Document ID: {result.get('document_id', 'N/A')}")
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.warning(f"[EMBEDDING] ⚠️ FAILED: Failed to create embeddings for document_id: {document_id}")
                logger.warning(f"[EMBEDDING] Error details: {error_msg}")
    
    except httpx.TimeoutException:
        logger.error(f"[EMBEDDING] ❌ TIMEOUT: Timeout calling AI service for document_id: {document_id} (timeout: 300s)")
    except httpx.HTTPStatusError as e:
        logger.error(f"[EMBEDDING] ❌ HTTP ERROR: HTTP error calling AI service for document_id: {document_id}")
        logger.error(f"[EMBEDDING] Status Code: {e.response.status_code}, Response: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"[EMBEDDING] ❌ REQUEST ERROR: Failed to connect to AI service for document_id: {document_id}")
        logger.error(f"[EMBEDDING] Error: {str(e)}")
    except Exception as e:
        logger.error(f"[EMBEDDING] ❌ UNEXPECTED ERROR: Error calling AI service for document_id: {document_id}")
        logger.error(f"[EMBEDDING] Error: {str(e)}", exc_info=True)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK
)
async def upload_document(
    request: Base64UploadRequest = Body(..., description="Base64 encoded document upload request"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a base64 encoded document to Cloudinary and save it to study_materials database.
    
    Supports various file types including PDFs, images, videos, and other documents.
    The file should be base64 encoded and included in the request body.
    Requires: class_id, subject_id, teacher_id, title, and optionally description.
    """
    logger.info(f"📥 Received document upload request - Filename: {request.filename}, Title: {request.title}")
    logger.info(f"📋 Request details - Class ID: {request.class_id}, Subject ID: {request.subject_id}, Teacher ID: {request.teacher_id}")
    
    try:
        # Decode base64 string
        try:
            # Get the base64 string from fileUrl field
            file_base64 = request.fileUrl
            
            # Handle base64 strings with or without data URI prefix
            if file_base64.startswith('data:'):
                # Remove data URI prefix (e.g., "data:application/pdf;base64,")
                base64_data = file_base64.split(',', 1)[1]
            else:
                base64_data = file_base64
            
            # Remove any whitespace or newlines
            base64_data = base64_data.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Add padding if needed (base64 strings must be multiple of 4)
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            
            file_bytes = base64.b64decode(base64_data, validate=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        # Use default folder if not provided
        upload_folder = request.folder or "tuition_master/documents"
        
        logger.info(f"☁️ Uploading file to Cloudinary - Folder: {upload_folder}, Resource Type: {request.resource_type}")
        
        # Upload to Cloudinary (public_id will be auto-generated by Cloudinary)
        result = upload_file_from_bytes(
            file_bytes=file_bytes,
            filename=request.filename,
            folder=upload_folder,
            resource_type=request.resource_type,
            public_id=None,  # Let Cloudinary auto-generate the public_id
            overwrite=False
        )
        
        if not result.get("success"):
            logger.error(f"❌ Cloudinary upload failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"✅ File uploaded to Cloudinary successfully - URL: {result.get('url')}, Public ID: {result.get('public_id')}")
        
        # Get file extension for file_type
        file_extension = request.filename.split('.')[-1].lower() if '.' in request.filename else 'unknown'
        
        # Create study material record in database
        study_material = models.StudyMaterial(
            class_id=request.class_id,
            subject_id=request.subject_id,
            teacher_id=request.teacher_id,
            title=request.title,
            description=request.description,
            file_url=result.get("url"),
            public_id=result.get("public_id"),  # Store Cloudinary public_id
            file_type=file_extension,
            file_size=result.get("bytes")
        )
        
        db.add(study_material)
        db.commit()
        db.refresh(study_material)
        
        logger.info(f"✅ Study material saved to database - ID: {study_material.id}, Title: {request.title}")
        logger.info(f"📁 Cloudinary URL: {result.get('url')}, Public ID: {result.get('public_id')}")
        
        # Get subject name and class grade from database for embeddings
        subject = db.query(models.Subject).filter(models.Subject.id == request.subject_id).first()
        class_obj = db.query(models.Class).filter(models.Class.id == request.class_id).first()
        
        # Trigger background task to create embeddings (only for PDF files)
        if file_extension.lower() == 'pdf' and subject and class_obj:
            logger.info(f"📄 PDF file detected - Scheduling embedding creation in background")
            logger.info(f"📋 Embedding params - Subject: {subject.name}, Class: {class_obj.grade}, Title: {request.title}")
            
            background_tasks.add_task(
                create_embeddings_async,
                file_url=result.get("url"),
                document_id=str(study_material.id),
                subject_name=subject.name,
                class_level=class_obj.grade,
                title=request.title,
                filename=request.filename
            )
            logger.info(f"✅ Background task scheduled for embedding creation - study_material_id: {study_material.id}")
        elif file_extension.lower() != 'pdf':
            logger.info(f"⏭️ Skipping embeddings for non-PDF file type: {file_extension}")
        else:
            logger.warning(f"⚠️ Could not find subject or class for study_material_id: {study_material.id} - Embeddings will not be created")
            if not subject:
                logger.warning(f"⚠️ Subject not found with ID: {request.subject_id}")
            if not class_obj:
                logger.warning(f"⚠️ Class not found with ID: {request.class_id}")
        
        # Ensure public_id is included in response
        public_id = result.get("public_id")
        if not public_id:
            logger.warning(f"⚠️ No public_id returned from Cloudinary for study_material_id: {study_material.id}")
        
        logger.info(f"📤 Returning response to client - study_material_id: {study_material.id}, public_id: {public_id}")
        
        return DocumentUploadResponse(
            success=True,
            url=result.get("url"),
            public_id=public_id,  # Explicitly include public_id
            format=result.get("format"),
            resource_type=result.get("resource_type"),
            bytes=result.get("bytes"),
            width=result.get("width"),
            height=result.get("height"),
            created_at=result.get("created_at"),
            study_material_id=study_material.id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Rollback database transaction on error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.post(
    "/upload-multipart",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK
)
async def upload_document_multipart(
    file: UploadFile = File(..., description="File to upload"),
    folder: Optional[str] = Form(None, description="Cloudinary folder path (default: tuition_master/documents)"),
    resource_type: str = Form("auto", description="Resource type: auto, image, raw, video"),
    public_id: Optional[str] = Form(None, description="Optional public ID for the file"),
    overwrite: bool = Form(False, description="Whether to overwrite existing files")
):
    """
    Upload a document via multipart form data to Cloudinary and get back the file URL.
    
    Alternative endpoint for traditional file uploads (multipart/form-data).
    Supports various file types including PDFs, images, videos, and other documents.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Use default folder if not provided
        upload_folder = folder or "tuition_master/documents"
        
        # Upload to Cloudinary
        result = upload_file_from_bytes(
            file_bytes=file_content,
            filename=file.filename or "document",
            folder=upload_folder,
            resource_type=resource_type,
            public_id=public_id,
            overwrite=overwrite
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {result.get('error', 'Unknown error')}"
            )
        
        return DocumentUploadResponse(
            success=True,
            url=result.get("url"),
            public_id=result.get("public_id"),
            format=result.get("format"),
            resource_type=result.get("resource_type"),
            bytes=result.get("bytes"),
            width=result.get("width"),
            height=result.get("height"),
            created_at=result.get("created_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.post(
    "/upload-from-path",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK
)
async def upload_document_from_path(
    file_path: str = Form(..., description="Local file path to upload"),
    folder: Optional[str] = Form(None, description="Cloudinary folder path (default: tuition_master/documents)"),
    resource_type: str = Form("auto", description="Resource type: auto, image, raw, video"),
    public_id: Optional[str] = Form(None, description="Optional public ID for the file"),
    overwrite: bool = Form(False, description="Whether to overwrite existing files")
):
    """
    Upload a document from a local file path to Cloudinary.
    
    Note: This endpoint requires the file to exist on the server's filesystem.
    """
    try:
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
        
        # Use default folder if not provided
        upload_folder = folder or "tuition_master/documents"
        
        # Import here to avoid circular imports
        from app.utils.cloudinary import upload_file
        
        # Upload to Cloudinary
        result = upload_file(
            file_path=file_path,
            folder=upload_folder,
            resource_type=resource_type,
            public_id=public_id,
            overwrite=overwrite
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {result.get('error', 'Unknown error')}"
            )
        
        return DocumentUploadResponse(
            success=True,
            url=result.get("url"),
            public_id=result.get("public_id"),
            format=result.get("format"),
            resource_type=result.get("resource_type"),
            bytes=result.get("bytes"),
            width=result.get("width"),
            height=result.get("height"),
            created_at=result.get("created_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.delete(
    "/delete/{public_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK
)
async def delete_document(
    public_id: str,
    resource_type: str = Query("auto", description="Resource type: auto, image, raw, video")
):
    """
    Delete a document from Cloudinary using its public_id.
    
    The public_id should include the folder path if the file was uploaded to a folder.
    Example: "tuition_master/documents/my_file"
    """
    try:
        result = delete_file(public_id=public_id, resource_type=resource_type)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {result.get('error', 'Unknown error')}"
            )
        
        return DocumentDeleteResponse(
            success=True,
            result=result.get("result")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )


@router.get(
    "/url/{public_id}",
    response_model=DocumentURLResponse,
    status_code=status.HTTP_200_OK
)
async def get_document_url(
    public_id: str,
    resource_type: str = Query("auto", description="Resource type: auto, image, raw, video")
):
    """
    Get the URL for a document stored in Cloudinary using its public_id.
    
    The public_id should include the folder path if the file was uploaded to a folder.
    Example: "tuition_master/documents/my_file"
    """
    try:
        url = get_file_url(public_id=public_id, resource_type=resource_type)
        
        return DocumentURLResponse(
            url=url,
            public_id=public_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting file URL: {str(e)}"
        )

