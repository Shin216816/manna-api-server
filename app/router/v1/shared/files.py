from fastapi import APIRouter, UploadFile, File, Query
from app.controller.shared.files import (
    upload_file_controller, delete_file_controller, get_file_url_controller
)
from app.core.responses import SuccessResponse

files_router = APIRouter(tags=["File Management"])

@files_router.post("/upload", response_model=SuccessResponse)
async def upload_file_route(
    file: UploadFile = File(...),
    file_type: str = Query(default="document", description="Type of file being uploaded")
):
    """Upload file"""
    return upload_file_controller(file, file_type)

@files_router.get("/{file_id}", response_model=SuccessResponse)
async def get_file_route(
    file_id: str
):
    """Get file details"""
    return get_file_url_controller(file_id)

@files_router.delete("/{file_id}", response_model=SuccessResponse)
async def delete_file_route(
    file_id: str
):
    """Delete file"""
    return delete_file_controller(file_id)
