from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, Query, Body, Depends, BackgroundTasks
from typing import Optional
import tempfile
import os
import base64
import httpx
import logging
import threading
import asyncio
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

# Configure logger to ensure it outputs to console
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
    This runs in a separate thread and doesn't block the API response.
    """
    thread_id = threading.current_thread().ident
    logger.info(f"[EMBEDDING] 🚀 [Thread-{thread_id}] Starting embedding creation process for document_id: {document_id}")
    print(f"[EMBEDDING] 🚀 [Thread-{thread_id}] Starting embedding creation process for document_id: {document_id}")
    logger.info(f"[EMBEDDING] [Thread-{thread_id}] Details - Subject: {subject_name}, Class: {class_level}, Title: {title}, Filename: {filename}")
    print(f"[EMBEDDING] [Thread-{thread_id}] Details - Subject: {subject_name}, Class: {class_level}, Title: {title}, Filename: {filename}")
    
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
        
        logger.info(f"[EMBEDDING] [Thread-{thread_id}] Calling AI service webhook: {webhook_url}")
        print(f"[EMBEDDING] [Thread-{thread_id}] Calling AI service webhook: {webhook_url}")
        logger.debug(f"[EMBEDDING] [Thread-{thread_id}] Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for large files
            logger.info(f"[EMBEDDING] [Thread-{thread_id}] Sending POST request to AI service...")
            print(f"[EMBEDDING] [Thread-{thread_id}] Sending POST request to AI service...")
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                logger.info(f"[EMBEDDING] ✅ [Thread-{thread_id}] SUCCESS: Embeddings created successfully for document_id: {document_id}")
                print(f"[EMBEDDING] ✅ [Thread-{thread_id}] SUCCESS: Embeddings created successfully for document_id: {document_id}")
                logger.info(f"[EMBEDDING] [Thread-{thread_id}] Response: {result.get('message', 'N/A')}, Document ID: {result.get('document_id', 'N/A')}")
                print(f"[EMBEDDING] [Thread-{thread_id}] Response: {result.get('message', 'N/A')}, Document ID: {result.get('document_id', 'N/A')}")
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.warning(f"[EMBEDDING] ⚠️ [Thread-{thread_id}] FAILED: Failed to create embeddings for document_id: {document_id}")
                print(f"[EMBEDDING] ⚠️ [Thread-{thread_id}] FAILED: Failed to create embeddings for document_id: {document_id}")
                logger.warning(f"[EMBEDDING] [Thread-{thread_id}] Error details: {error_msg}")
                print(f"[EMBEDDING] [Thread-{thread_id}] Error details: {error_msg}")
    
    except httpx.TimeoutException:
        logger.error(f"[EMBEDDING] ❌ [Thread-{thread_id}] TIMEOUT: Timeout calling AI service for document_id: {document_id} (timeout: 300s)")
        print(f"[EMBEDDING] ❌ [Thread-{thread_id}] TIMEOUT: Timeout calling AI service for document_id: {document_id} (timeout: 300s)")
    except httpx.HTTPStatusError as e:
        logger.error(f"[EMBEDDING] ❌ [Thread-{thread_id}] HTTP ERROR: HTTP error calling AI service for document_id: {document_id}")
        print(f"[EMBEDDING] ❌ [Thread-{thread_id}] HTTP ERROR: HTTP error calling AI service for document_id: {document_id}")
        logger.error(f"[EMBEDDING] [Thread-{thread_id}] Status Code: {e.response.status_code}, Response: {e.response.text}")
        print(f"[EMBEDDING] [Thread-{thread_id}] Status Code: {e.response.status_code}, Response: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"[EMBEDDING] ❌ [Thread-{thread_id}] REQUEST ERROR: Failed to connect to AI service for document_id: {document_id}")
        print(f"[EMBEDDING] ❌ [Thread-{thread_id}] REQUEST ERROR: Failed to connect to AI service for document_id: {document_id}")
        logger.error(f"[EMBEDDING] [Thread-{thread_id}] Error: {str(e)}")
        print(f"[EMBEDDING] [Thread-{thread_id}] Error: {str(e)}")
    except Exception as e:
        logger.error(f"[EMBEDDING] ❌ [Thread-{thread_id}] UNEXPECTED ERROR: Error calling AI service for document_id: {document_id}")
        print(f"[EMBEDDING] ❌ [Thread-{thread_id}] UNEXPECTED ERROR: Error calling AI service for document_id: {document_id}")
        logger.error(f"[EMBEDDING] [Thread-{thread_id}] Error: {str(e)}", exc_info=True)
        print(f"[EMBEDDING] [Thread-{thread_id}] Error: {str(e)}")
    finally:
        logger.info(f"[EMBEDDING] 🏁 [Thread-{thread_id}] Embedding task completed for document_id: {document_id}")
        print(f"[EMBEDDING] 🏁 [Thread-{thread_id}] Embedding task completed for document_id: {document_id}")


def run_embeddings_in_thread(
    file_url: str,
    document_id: str,
    subject_name: str,
    class_level: str,
    title: str,
    filename: str
):
    """
    Wrapper function to run the async embedding creation in a separate thread.
    This creates a new event loop in the thread and runs the async function.
    """
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    logger.info(f"[THREAD] 🧵 Starting new thread for embeddings - Thread ID: {thread_id}, Name: {thread_name}, Document ID: {document_id}")
    print(f"[THREAD] 🧵 Starting new thread for embeddings - Thread ID: {thread_id}, Name: {thread_name}, Document ID: {document_id}")
    
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function
        loop.run_until_complete(
            create_embeddings_async(
                file_url=file_url,
                document_id=document_id,
                subject_name=subject_name,
                class_level=class_level,
                title=title,
                filename=filename
            )
        )
    except Exception as e:
        logger.error(f"[THREAD] ❌ [Thread-{thread_id}] Error in thread execution: {str(e)}")
        print(f"[THREAD] ❌ [Thread-{thread_id}] Error in thread execution: {str(e)}")
    finally:
        # Clean up the event loop
        try:
            loop.close()
        except:
            pass
        logger.info(f"[THREAD] 🏁 [Thread-{thread_id}] Thread completed and cleaned up")
        print(f"[THREAD] 🏁 [Thread-{thread_id}] Thread completed and cleaned up")


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
    main_thread_id = threading.current_thread().ident
    logger.info(f"[UPLOAD] 📥 [Main-Thread-{main_thread_id}] Received document upload request - Filename: {request.filename}, Title: {request.title}")
    print(f"[UPLOAD] 📥 [Main-Thread-{main_thread_id}] Received document upload request - Filename: {request.filename}, Title: {request.title}")
    logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Request details - Class ID: {request.class_id}, Subject ID: {request.subject_id}, Teacher ID: {request.teacher_id}")
    print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Request details - Class ID: {request.class_id}, Subject ID: {request.subject_id}, Teacher ID: {request.teacher_id}")
    
    try:
        # Step 1: Decode base64 string
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 1: Decoding base64 string...")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 1: Decoding base64 string...")
        try:
            # Get the base64 string from fileUrl field
            file_base64 = request.fileUrl
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Base64 string length: {len(file_base64)} characters")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Base64 string length: {len(file_base64)} characters")
            
            # Handle base64 strings with or without data URI prefix
            if file_base64.startswith('data:'):
                # Remove data URI prefix (e.g., "data:application/pdf;base64,")
                base64_data = file_base64.split(',', 1)[1]
                logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Removed data URI prefix")
                print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Removed data URI prefix")
            else:
                base64_data = file_base64
            
            # Remove any whitespace or newlines
            base64_data = base64_data.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Add padding if needed (base64 strings must be multiple of 4)
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
                logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Added {4 - missing_padding} padding characters")
                print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Added {4 - missing_padding} padding characters")
            
            file_bytes = base64.b64decode(base64_data, validate=True)
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] ✅ Base64 decoded successfully - File size: {len(file_bytes)} bytes")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] ✅ Base64 decoded successfully - File size: {len(file_bytes)} bytes")
        except Exception as e:
            logger.error(f"[UPLOAD] ❌ [Main-Thread-{main_thread_id}] Base64 decoding failed: {str(e)}")
            print(f"[UPLOAD] ❌ [Main-Thread-{main_thread_id}] Base64 decoding failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        # Step 2: Upload to Cloudinary
        upload_folder = request.folder or "tuition_master/documents"
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 2: Uploading file to Cloudinary...")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 2: Uploading file to Cloudinary...")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary params - Folder: {upload_folder}, Resource Type: {request.resource_type}, Filename: {request.filename}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary params - Folder: {upload_folder}, Resource Type: {request.resource_type}, Filename: {request.filename}")
        
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
            logger.error(f"[UPLOAD] ❌ [Main-Thread-{main_thread_id}] Cloudinary upload failed: {result.get('error', 'Unknown error')}")
            print(f"[UPLOAD] ❌ [Main-Thread-{main_thread_id}] Cloudinary upload failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"[UPLOAD] ✅ [Main-Thread-{main_thread_id}] File uploaded to Cloudinary successfully")
        print(f"[UPLOAD] ✅ [Main-Thread-{main_thread_id}] File uploaded to Cloudinary successfully")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary URL: {result.get('url')}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary URL: {result.get('url')}")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Public ID: {result.get('public_id')}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Public ID: {result.get('public_id')}")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary format: {result.get('format')}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary format: {result.get('format')}")
        
        # Step 3: Save to database
        # Determine file extension from filename first, then fallback to Cloudinary format
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 3: Determining file extension...")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 3: Determining file extension...")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Original filename: '{request.filename}'")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Original filename: '{request.filename}'")
        
        # Try to get extension from filename
        if '.' in request.filename:
            file_extension_from_filename = request.filename.split('.')[-1].lower().strip()
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Extension from filename: '{file_extension_from_filename}'")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Extension from filename: '{file_extension_from_filename}'")
        else:
            file_extension_from_filename = None
            logger.warning(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] No extension found in filename: '{request.filename}'")
            print(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] No extension found in filename: '{request.filename}'")
        
        # Get format from Cloudinary response
        cloudinary_format = result.get('format', '').lower() if result.get('format') else None
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary detected format: '{cloudinary_format}'")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary detected format: '{cloudinary_format}'")
        
        # Determine final file extension: prefer filename extension, fallback to Cloudinary format
        if file_extension_from_filename and file_extension_from_filename != '':
            file_extension = file_extension_from_filename
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Using extension from filename: '{file_extension}'")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Using extension from filename: '{file_extension}'")
        elif cloudinary_format:
            file_extension = cloudinary_format
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Using extension from Cloudinary format: '{file_extension}'")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Using extension from Cloudinary format: '{file_extension}'")
        else:
            # Try to detect from base64 data URI if available
            file_base64 = request.fileUrl
            if file_base64.startswith('data:'):
                mime_type = file_base64.split(';')[0].split(':')[1]
                logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] MIME type from data URI: '{mime_type}'")
                print(f"[UPLOAD] [Main-Thread-{main_thread_id}] MIME type from data URI: '{mime_type}'")
                # Map common MIME types to extensions
                mime_to_ext = {
                    'application/pdf': 'pdf',
                    'image/jpeg': 'jpg',
                    'image/png': 'png',
                    'image/gif': 'gif',
                    'image/webp': 'webp',
                    'video/mp4': 'mp4',
                    'video/quicktime': 'mov',
                    'application/msword': 'doc',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                    'application/vnd.ms-excel': 'xls',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                    'text/plain': 'txt',
                    'text/csv': 'csv'
                }
                file_extension = mime_to_ext.get(mime_type, 'unknown')
                logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Extension from MIME type: '{file_extension}'")
                print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Extension from MIME type: '{file_extension}'")
            else:
                file_extension = 'unknown'
                logger.warning(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Could not determine file extension, using 'unknown'")
                print(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Could not determine file extension, using 'unknown'")
        
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Final file extension: '{file_extension}'")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Final file extension: '{file_extension}'")
        
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 3: Saving study material to database...")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 3: Saving study material to database...")
        
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
        
        logger.info(f"[UPLOAD] ✅ [Main-Thread-{main_thread_id}] Study material saved to database")
        print(f"[UPLOAD] ✅ [Main-Thread-{main_thread_id}] Study material saved to database")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Study Material ID: {study_material.id}, Title: {request.title}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Study Material ID: {study_material.id}, Title: {request.title}")
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary URL: {result.get('url')}, Public ID: {result.get('public_id')}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Cloudinary URL: {result.get('url')}, Public ID: {result.get('public_id')}")
        
        # Step 4: Schedule embedding creation in separate thread (only for PDF files)
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 4: Checking if embedding creation is needed...")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 4: Checking if embedding creation is needed...")
        
        # Get subject name and class grade from database for embeddings
        subject = db.query(models.Subject).filter(models.Subject.id == request.subject_id).first()
        class_obj = db.query(models.Class).filter(models.Class.id == request.class_id).first()
        
        if file_extension.lower() == 'pdf' and subject and class_obj:
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] 📄 PDF file detected - Creating separate thread for embedding creation")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] 📄 PDF file detected - Creating separate thread for embedding creation")
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Embedding params - Subject: {subject.name}, Class: {class_obj.grade}, Title: {request.title}")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Embedding params - Subject: {subject.name}, Class: {class_obj.grade}, Title: {request.title}")
            
            # Create a new thread for embedding creation (completely separate from main thread)
            embedding_thread = threading.Thread(
                target=run_embeddings_in_thread,
                args=(
                    result.get("url"),
                    str(study_material.id),
                    subject.name,
                    class_obj.grade,
                    request.title,
                    request.filename
                ),
                name=f"EmbeddingThread-{study_material.id}",
                daemon=True  # Daemon thread will be killed when main program exits
            )
            
            embedding_thread.start()
            logger.info(f"[UPLOAD] ✅ [Main-Thread-{main_thread_id}] Separate thread started for embedding creation - Thread Name: {embedding_thread.name}, Study Material ID: {study_material.id}")
            print(f"[UPLOAD] ✅ [Main-Thread-{main_thread_id}] Separate thread started for embedding creation - Thread Name: {embedding_thread.name}, Study Material ID: {study_material.id}")
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] ⚡ Main thread continues without blocking - Response will be sent immediately")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] ⚡ Main thread continues without blocking - Response will be sent immediately")
        elif file_extension.lower() != 'pdf':
            logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] ⏭️ Skipping embeddings for non-PDF file type: {file_extension}")
            print(f"[UPLOAD] [Main-Thread-{main_thread_id}] ⏭️ Skipping embeddings for non-PDF file type: {file_extension}")
        else:
            logger.warning(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Could not find subject or class for study_material_id: {study_material.id} - Embeddings will not be created")
            print(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Could not find subject or class for study_material_id: {study_material.id} - Embeddings will not be created")
            if not subject:
                logger.warning(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Subject not found with ID: {request.subject_id}")
                print(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Subject not found with ID: {request.subject_id}")
            if not class_obj:
                logger.warning(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Class not found with ID: {request.class_id}")
                print(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] Class not found with ID: {request.class_id}")
        
        # Step 5: Prepare response
        public_id = result.get("public_id")
        if not public_id:
            logger.warning(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] No public_id returned from Cloudinary for study_material_id: {study_material.id}")
            print(f"[UPLOAD] ⚠️ [Main-Thread-{main_thread_id}] No public_id returned from Cloudinary for study_material_id: {study_material.id}")
        
        logger.info(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 5: Preparing response...")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Step 5: Preparing response...")
        logger.info(f"[UPLOAD] 📤 [Main-Thread-{main_thread_id}] Returning response to client - study_material_id: {study_material.id}, public_id: {public_id}")
        print(f"[UPLOAD] 📤 [Main-Thread-{main_thread_id}] Returning response to client - study_material_id: {study_material.id}, public_id: {public_id}")
        
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
        logger.error(f"[UPLOAD] ❌ [Main-Thread-{main_thread_id}] Error uploading document: {str(e)}")
        print(f"[UPLOAD] ❌ [Main-Thread-{main_thread_id}] Error uploading document: {str(e)}")
        import traceback
        logger.error(f"[UPLOAD] [Main-Thread-{main_thread_id}] Traceback: {traceback.format_exc()}")
        print(f"[UPLOAD] [Main-Thread-{main_thread_id}] Traceback: {traceback.format_exc()}")
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
    "/url",
    response_model=DocumentURLResponse,
    status_code=status.HTTP_200_OK
)
async def get_document_url(
    public_id: str = Query(..., description="Public ID of the document (can include folder path, e.g., 'tuition_master/documents/my_file')"),
    resource_type: str = Query("auto", description="Resource type: auto, image, raw, video")
):
    """
    Get the URL for a document stored in Cloudinary using its public_id.
    
    The public_id should include the folder path if the file was uploaded to a folder.
    Example: "tuition_master/documents/my_file"
    
    Note: Use query parameter instead of path parameter to support public_ids with slashes.
    """
    thread_id = threading.current_thread().ident
    logger.info(f"[VIEW] 📄 [Thread-{thread_id}] View document request received - Public ID: {public_id}, Resource Type: {resource_type}")
    print(f"[VIEW] 📄 [Thread-{thread_id}] View document request received - Public ID: {public_id}, Resource Type: {resource_type}")
    
    try:
        logger.info(f"[VIEW] [Thread-{thread_id}] Step 1: Fetching document URL from Cloudinary...")
        print(f"[VIEW] [Thread-{thread_id}] Step 1: Fetching document URL from Cloudinary...")
        logger.info(f"[VIEW] [Thread-{thread_id}] Cloudinary params - Public ID: {public_id}, Resource Type: {resource_type}")
        print(f"[VIEW] [Thread-{thread_id}] Cloudinary params - Public ID: {public_id}, Resource Type: {resource_type}")
        
        url = get_file_url(public_id=public_id, resource_type=resource_type)
        
        logger.info(f"[VIEW] ✅ [Thread-{thread_id}] Document URL retrieved successfully")
        print(f"[VIEW] ✅ [Thread-{thread_id}] Document URL retrieved successfully")
        logger.info(f"[VIEW] [Thread-{thread_id}] Public ID: {public_id}")
        print(f"[VIEW] [Thread-{thread_id}] Public ID: {public_id}")
        logger.info(f"[VIEW] [Thread-{thread_id}] URL: {url}")
        print(f"[VIEW] [Thread-{thread_id}] URL: {url}")
        logger.info(f"[VIEW] 📤 [Thread-{thread_id}] Returning response to client")
        print(f"[VIEW] 📤 [Thread-{thread_id}] Returning response to client")
        
        return DocumentURLResponse(
            url=url,
            public_id=public_id
        )
    
    except Exception as e:
        logger.error(f"[VIEW] ❌ [Thread-{thread_id}] Error getting file URL for public_id: {public_id}")
        print(f"[VIEW] ❌ [Thread-{thread_id}] Error getting file URL for public_id: {public_id}")
        logger.error(f"[VIEW] [Thread-{thread_id}] Error details: {str(e)}")
        print(f"[VIEW] [Thread-{thread_id}] Error details: {str(e)}")
        import traceback
        logger.error(f"[VIEW] [Thread-{thread_id}] Traceback: {traceback.format_exc()}")
        print(f"[VIEW] [Thread-{thread_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting file URL: {str(e)}"
        )

