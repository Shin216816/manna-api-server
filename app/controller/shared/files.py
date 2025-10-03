from fastapi import HTTPException, UploadFile
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.responses import ResponseFactory
from app.utils.file_upload import (
    upload_file,
    delete_file,
    get_file_url as get_file_info,
)


def upload_file_controller(file: UploadFile, file_type: str = "document"):
    """Upload a file to storage"""
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        # Upload file using the new utility
        result = upload_file(file, file_type)

        return ResponseFactory.success(
            message="File uploaded successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file")


def delete_file_controller(file_url: str):
    """Delete a file from storage"""
    try:
        result = delete_file(file_url)

        return ResponseFactory.success(message="File deleted successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete file")


def get_file_url_controller(file_url: str):
    """Get file information"""
    try:
        result = get_file_info(file_url)

        return ResponseFactory.success(
            message="File information retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get file information")
