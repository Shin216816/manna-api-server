"""
Church KYC Compliance Router

Handles comprehensive KYC compliance endpoints:
- Complete KYC submission with all required documents
- Beneficial ownership disclosure
- Compliance attestations
- Document upload and verification
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.controller.church.kyc_compliance import (
    submit_comprehensive_kyc,
    upload_kyc_document,
    get_kyc_compliance_status
)
from app.schema.church_schema import ChurchKYCRequest, KYCStatusResponse
from app.core.responses import ResponseFactory
from app.middleware.auth_middleware import get_current_user
from app.utils.database import get_db

# Important: Do not set a prefix here; aggregator mounts at /church/kyc
router = APIRouter(tags=["Church KYC Compliance"])


@router.post("/submit", response_model=None)
async def submit_kyc_compliance(
    church_id: int,
    kyc_data: ChurchKYCRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit comprehensive KYC compliance information
    
    This endpoint handles the complete KYC submission process including:
    - Legal entity information
    - Beneficial ownership disclosure
    - Required document uploads
    - Compliance attestations
    """
    return submit_comprehensive_kyc(church_id, kyc_data, db)


@router.post("/upload-document", response_model=None)
async def upload_compliance_document(
    church_id: int,
    document_type: str = Form(..., description="Type of document to upload"),
    file: UploadFile = File(..., description="Document file"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload KYC compliance documents
    
    Supported document types:
    - articles_of_incorporation
    - tax_exempt_letter
    - bank_statement
    - board_resolution
    - gov_id_front
    - gov_id_back
    """
    return upload_kyc_document(church_id, document_type, file, db)


@router.get("/status", response_model=None)
async def get_compliance_status(
    church_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive KYC compliance status
    
    Returns detailed compliance status including:
    - Completion percentage
    - Required documents status
    - Compliance attestations
    - Beneficial owners information
    """
    return get_kyc_compliance_status(church_id, db)


@router.get("/checklist", response_model=None)
async def get_compliance_checklist(
    church_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get KYC compliance checklist with completion status
    
    Returns a detailed checklist showing what's completed and what's missing
    for KYC compliance.
    """
    return get_kyc_compliance_status(church_id, db)