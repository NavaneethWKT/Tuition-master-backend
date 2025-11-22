import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


def upload_file(
    file_path: str,
    folder: Optional[str] = "tuition_master/documents",
    resource_type: str = "auto",
    public_id: Optional[str] = None,
    overwrite: bool = False,
    invalidate: bool = True
) -> dict:
    """
    Upload a file to Cloudinary
    
    Args:
        file_path: Path to the file to upload
        folder: Folder path in Cloudinary (default: "tuition_master/documents")
        resource_type: Type of resource (auto, image, raw, video)
        public_id: Optional public ID for the file
        overwrite: Whether to overwrite existing files
        invalidate: Whether to invalidate CDN cache
    
    Returns:
        dict: Upload response containing URL and other metadata
    """
    try:
        upload_options = {
            "folder": folder,
            "resource_type": resource_type,
            "overwrite": overwrite,
            "invalidate": invalidate
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        result = cloudinary.uploader.upload(
            file_path,
            **upload_options
        )
        
        return {
            "success": True,
            "url": result.get("secure_url") or result.get("url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "resource_type": result.get("resource_type"),
            "bytes": result.get("bytes"),
            "width": result.get("width"),
            "height": result.get("height"),
            "created_at": result.get("created_at")
        }
    except Exception as e:
        logger.error(f"Error uploading file to Cloudinary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def upload_file_from_bytes(
    file_bytes: bytes,
    filename: str,
    folder: Optional[str] = "tuition_master/documents",
    resource_type: str = "auto",
    public_id: Optional[str] = None,
    overwrite: bool = False,
    invalidate: bool = True
) -> dict:
    """
    Upload a file to Cloudinary from bytes
    
    Args:
        file_bytes: File content as bytes
        filename: Original filename
        folder: Folder path in Cloudinary (default: "tuition_master/documents")
        resource_type: Type of resource (auto, image, raw, video)
        public_id: Optional public ID for the file
        overwrite: Whether to overwrite existing files
        invalidate: Whether to invalidate CDN cache
    
    Returns:
        dict: Upload response containing URL and other metadata
    """
    try:
        upload_options = {
            "folder": folder,
            "resource_type": resource_type,
            "overwrite": overwrite,
            "invalidate": invalidate
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        result = cloudinary.uploader.upload(
            file_bytes,
            filename=filename,
            **upload_options
        )
        
        return {
            "success": True,
            "url": result.get("secure_url") or result.get("url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "resource_type": result.get("resource_type"),
            "bytes": result.get("bytes"),
            "width": result.get("width"),
            "height": result.get("height"),
            "created_at": result.get("created_at")
        }
    except Exception as e:
        logger.error(f"Error uploading file to Cloudinary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_file(public_id: str, resource_type: str = "auto") -> dict:
    """
    Delete a file from Cloudinary
    
    Args:
        public_id: Public ID of the file to delete
        resource_type: Type of resource (auto, image, raw, video)
    
    Returns:
        dict: Deletion response
    """
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type,
            invalidate=True
        )
        
        return {
            "success": result.get("result") == "ok",
            "result": result.get("result")
        }
    except Exception as e:
        logger.error(f"Error deleting file from Cloudinary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_file_url(public_id: str, resource_type: str = "auto", transformation: Optional[dict] = None) -> str:
    """
    Generate a URL for a Cloudinary file
    
    Args:
        public_id: Public ID of the file
        resource_type: Type of resource (auto, image, raw, video)
        transformation: Optional transformation parameters
    
    Returns:
        str: File URL
    """
    try:
        url = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            secure=True,
            **transformation if transformation else {}
        )
        return url[0]
    except Exception as e:
        logger.error(f"Error generating file URL: {str(e)}")
        raise

