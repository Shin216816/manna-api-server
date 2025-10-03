"""
File Upload Utilities

Handles file uploads and management for the Manna backend.
Currently uses local storage with option to integrate cloud storage later.
"""

import os
import shutil
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException

from app.config import config

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Create subdirectories
PROFILE_IMAGES_DIR = UPLOADS_DIR / "profile_images"
CHURCH_DOCS_DIR = UPLOADS_DIR / "church_docs"
CHURCH_LOGOS_DIR = UPLOADS_DIR / "church_logos"
DOCUMENTS_DIR = UPLOADS_DIR / "documents"

for directory in [PROFILE_IMAGES_DIR, CHURCH_DOCS_DIR, CHURCH_LOGOS_DIR, DOCUMENTS_DIR]:
    directory.mkdir(exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent conflicts"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = Path(original_filename).suffix
    return f"{timestamp}_{unique_id}{file_extension}"


def validate_file_type(file: UploadFile, allowed_types: list) -> bool:
    """Validate file type"""
    if not file.content_type:
        return False
    return file.content_type in allowed_types


def validate_file_size(file: UploadFile, max_size_mb: int = 10) -> bool:
    """Validate file size"""
    # For UploadFile, size might be None until file is read
    # We'll skip size validation here and let the controller handle it after reading
    return True


def save_file_locally(file: UploadFile, directory: Path, filename: str) -> str:
    """Save file to local storage"""
    try:
        
        file_path = directory / filename
        
        
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)
        
        
        # Ensure file pointer is at the beginning
        
        file.file.seek(0)
        
        
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Verify file was written
        if file_path.exists():
            file_size = file_path.stat().st_size
        else:
            
            raise Exception("File was not created")
        
        # Return full URL for local storage
        from app.config import config
        base_url = config.BASE_URL.rstrip('/')
        
        # For local development, use localhost instead of production URL
        if config.ENVIRONMENT == "development" and "localhost" not in base_url and "127.0.0.1" not in base_url:
            base_url = f"http://localhost:{config.PORT}"
        
        url = f"{base_url}/uploads/{directory.name}/{filename}"
        return url
    except Exception as e:
        
        import traceback

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


def delete_file_locally(file_url: str) -> bool:
    """Delete file from local storage"""
    try:
        if not file_url:
            return False
        
        # Handle both full URLs and relative paths
        if file_url.startswith("http"):
            from urllib.parse import urlparse
            parsed_url = urlparse(file_url)
            relative_path = parsed_url.path
        else:
            relative_path = file_url
        
        # Check if it's a valid uploads path
        if not relative_path.startswith("/uploads/"):
            return False
        
        # Extract file path from URL
        file_path = relative_path.replace("/uploads/", "")
        full_path = UPLOADS_DIR / file_path
        
        if full_path.exists():
            full_path.unlink()
            return True
        else:
            return False
    except Exception as e:
        
        return False


def upload_file(file: UploadFile, file_type: str = "document", directory: Optional[str] = None) -> dict:
    """Upload file to local storage"""
    try:
        # Validate file
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # File size validation is handled in the controller after reading the file
        
        # Determine upload directory based on file type
        if file_type == "profile_image":
            upload_dir = PROFILE_IMAGES_DIR
            allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        elif file_type == "church_logo":
            upload_dir = CHURCH_LOGOS_DIR
            allowed_types = ["image/jpeg", "image/png", "image/gif"]
        elif file_type == "church_document":
            upload_dir = CHURCH_DOCS_DIR
            allowed_types = ["application/pdf", "image/jpeg", "image/png"]
        else:
            upload_dir = DOCUMENTS_DIR
            allowed_types = ["application/pdf", "image/jpeg", "image/png", "text/plain"]
        
        # Validate file type
        if not validate_file_type(file, allowed_types):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Save file locally
        file_url = save_file_locally(file, upload_dir, filename)
        
        return {
            "success": True,
            "url": file_url,
            "filename": filename,
            "size": file.size or 0,
            "content_type": file.content_type
        }
        
    except HTTPException:    
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


def delete_file(file_url: str) -> dict:
    """Delete file from local storage"""
    try:
        success = delete_file_locally(file_url)
        
        if success:
            return {
                "success": True,
                "message": "File deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(
            status_code=500,
            detail="Failed to delete file"
        )


def get_file_url(file_url: str) -> dict:
    """Get file information"""
    try:
        if not file_url or not file_url.startswith("/uploads/"):
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        # Extract file path from URL
        file_path = file_url.replace("/uploads/", "")
        full_path = UPLOADS_DIR / file_path
        
        if not full_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        return {
            "success": True,
            "url": file_url,
            "filename": full_path.name,
            "size": full_path.stat().st_size,
            "exists": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get file information"
        )


# Legacy functions for backward compatibility (now use local storage)
def upload_file_to_s3(file: UploadFile, filename: str, bucket: str = "manna-uploads") -> dict:
    """Upload file to local storage (replaces S3)"""
    return upload_file(file, "document")


def delete_file_from_s3(file_url: str, bucket: str = "manna-uploads") -> bool:
    """Delete file from local storage (replaces S3)"""
    try:
        result = delete_file(file_url)
        return result["success"]
    except:
        return False
