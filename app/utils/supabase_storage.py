from supabase import create_client, Client
from app.config import settings
from typing import Optional
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global supabase
    if supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be configured in .env file")
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info(f"☁️ Supabase Storage configured - URL: {settings.SUPABASE_URL}, Bucket: {settings.SUPABASE_STORAGE_BUCKET}")
    return supabase


def upload_file_from_bytes(
    file_bytes: bytes,
    filename: str,
    folder: Optional[str] = "tuition_master/documents",
    public_id: Optional[str] = None,
    overwrite: bool = False
) -> dict:
    """
    Upload a file to Supabase Storage from bytes
    
    Args:
        file_bytes: File content as bytes
        filename: Original filename
        folder: Folder path in storage (default: "tuition_master/documents")
        public_id: Optional custom file path/name (without extension)
        overwrite: Whether to overwrite existing files
    
    Returns:
        dict: Upload response containing URL and other metadata
    """
    try:
        client = get_supabase_client()
        bucket = settings.SUPABASE_STORAGE_BUCKET
        
        # Generate file path
        if public_id:
            # Use public_id as the path (add folder if needed)
            if folder:
                file_path = f"{folder}/{public_id}"
            else:
                file_path = public_id
        else:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_id = str(uuid.uuid4())
            if folder:
                file_path = f"{folder}/{unique_id}.{file_extension}" if file_extension else f"{folder}/{unique_id}"
            else:
                file_path = f"{unique_id}.{file_extension}" if file_extension else unique_id
        
        # Check if file exists and handle overwrite
        if not overwrite:
            try:
                existing = client.storage.from_(bucket).list(file_path)
                if existing:
                    # File exists, generate new unique name
                    file_extension = filename.split('.')[-1] if '.' in filename else ''
                    unique_id = str(uuid.uuid4())
                    if folder:
                        file_path = f"{folder}/{unique_id}.{file_extension}" if file_extension else f"{folder}/{unique_id}"
                    else:
                        file_path = f"{unique_id}.{file_extension}" if file_extension else unique_id
            except Exception:
                # File doesn't exist, proceed
                pass
        
        # Upload file
        response = client.storage.from_(bucket).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": _get_content_type(filename), "upsert": overwrite}
        )
        
        # Get public URL
        url_response = client.storage.from_(bucket).get_public_url(file_path)
        public_url = url_response
        
        logger.info(f"✅ File uploaded to Supabase Storage - Path: {file_path}, URL: {public_url}")
        
        return {
            "success": True,
            "url": public_url,
            "public_id": file_path,  # Use file_path as public_id for Supabase
            "format": filename.split('.')[-1] if '.' in filename else 'unknown',
            "resource_type": "raw",
            "bytes": len(file_bytes),
            "width": None,
            "height": None,
            "created_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Error uploading file to Supabase Storage: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def delete_file(public_id: str, bucket: Optional[str] = None) -> dict:
    """
    Delete a file from Supabase Storage
    
    Args:
        public_id: File path in storage (the public_id stored in database)
        bucket: Optional bucket name (defaults to configured bucket)
    
    Returns:
        dict: Delete response
    """
    try:
        client = get_supabase_client()
        bucket_name = bucket or settings.SUPABASE_STORAGE_BUCKET
        
        # Delete file
        response = client.storage.from_(bucket_name).remove([public_id])
        
        logger.info(f"✅ File deleted from Supabase Storage - Path: {public_id}")
        
        return {
            "success": True,
            "result": "File deleted successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Error deleting file from Supabase Storage: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def get_file_url(public_id: str, bucket: Optional[str] = None, expires_in: int = 3600) -> str:
    """
    Get the public URL for a file in Supabase Storage
    
    Args:
        public_id: File path in storage (the public_id stored in database)
        bucket: Optional bucket name (defaults to configured bucket)
        expires_in: URL expiration time in seconds (for signed URLs, default: 1 hour)
    
    Returns:
        str: Public URL of the file
    """
    try:
        client = get_supabase_client()
        bucket_name = bucket or settings.SUPABASE_STORAGE_BUCKET
        
        # Get public URL
        url = client.storage.from_(bucket_name).get_public_url(public_id)
        
        logger.info(f"✅ Generated Supabase Storage URL - Path: {public_id}, URL: {url}")
        
        return url
    
    except Exception as e:
        logger.error(f"❌ Error generating file URL from Supabase Storage: {str(e)}", exc_info=True)
        raise


def _get_content_type(filename: str) -> str:
    """Get content type based on file extension"""
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    content_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'mp4': 'video/mp4',
        'mp3': 'audio/mpeg',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'txt': 'text/plain',
        'csv': 'text/csv',
    }
    return content_types.get(extension, 'application/octet-stream')

