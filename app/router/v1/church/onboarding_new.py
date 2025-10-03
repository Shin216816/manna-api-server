from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.controller.church.onboarding import (
    submit_church_onboarding,
    get_church_onboarding_status,
    update_stripe_onboarding_status,
    complete_church_onboarding
)
from app.controller.church.onboarding import (
    submit_beneficial_owners, 
    upload_church_documents,
    get_kyc_progress,
    submit_church_kyc,
    submit_final_kyc
)
from app.schema.church_schema import ChurchOnboardingRequest, ControlPersonRequest, ChurchKYCRequest
from app.core.responses import SuccessResponse

onboarding_router = APIRouter(tags=["Church Onboarding"])

@onboarding_router.post("/submit", response_model=SuccessResponse)
async def submit_onboarding_route(
    data: ChurchOnboardingRequest,
    db: Session = Depends(get_db)
):
    """Submit combined church profile and KYC information, create Stripe Connect account"""
    return submit_church_onboarding(data, db)

@onboarding_router.get("/status/{church_id}", response_model=SuccessResponse)
async def get_onboarding_status_route(
    church_id: int,
    db: Session = Depends(get_db)
):
    """Get church onboarding status including KYC and Stripe status"""
    return get_church_onboarding_status(church_id, db)

@onboarding_router.put("/stripe-status/{church_id}", response_model=SuccessResponse)
async def update_stripe_status_route(
    church_id: int,
    stripe_data: dict,
    db: Session = Depends(get_db)
):
    """Update Stripe onboarding status after completion"""
    return update_stripe_onboarding_status(church_id, stripe_data, db)

@onboarding_router.post("/beneficial-owners/{church_id}", response_model=SuccessResponse)
async def submit_beneficial_owners_route(
    church_id: int,
    control_persons: List[ControlPersonRequest],
    db: Session = Depends(get_db)
):
    """Submit beneficial owners/control persons for KYC"""
    return submit_beneficial_owners(church_id, control_persons, db)

@onboarding_router.post("/complete/{church_id}", response_model=SuccessResponse)
async def complete_onboarding_route(
    church_id: int,
    db: Session = Depends(get_db)
):
    """Complete church onboarding and generate auth token"""
    return complete_church_onboarding(church_id, db)

@onboarding_router.post("/documents/{church_id}")
async def upload_documents_route(
    church_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload church documents for KYC verification"""
    return upload_church_documents(church_id, document_type, file, db)

# New KYC step-by-step endpoints
@onboarding_router.get("/kyc/progress/{church_id}", response_model=SuccessResponse)
async def get_kyc_progress_route(
    church_id: int,
    db: Session = Depends(get_db)
):
    """Get KYC progress and current step"""
    return get_kyc_progress(church_id, db)

@onboarding_router.post("/kyc/legal-info/{church_id}", response_model=SuccessResponse)
async def submit_legal_info_route(
    church_id: int,
    data: ChurchKYCRequest,
    db: Session = Depends(get_db)
):
    """Submit legal information (Step 1 of KYC)"""
    return submit_church_kyc(church_id, data, db)

@onboarding_router.post("/kyc/beneficial-owners/{church_id}", response_model=SuccessResponse)
async def submit_beneficial_owners_kyc_route(
    church_id: int,
    control_persons: List[ControlPersonRequest],
    db: Session = Depends(get_db)
):
    """Submit beneficial owners (Step 2 of KYC)"""
    return submit_beneficial_owners(church_id, control_persons, db)

@onboarding_router.post("/kyc/documents/{church_id}", response_model=SuccessResponse)
async def upload_kyc_documents_route(
    church_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload KYC documents (Step 3 of KYC)"""
    return upload_church_documents(church_id, document_type, file, db)

@onboarding_router.post("/kyc/submit/{church_id}", response_model=SuccessResponse)
async def submit_final_kyc_route(
    church_id: int,
    db: Session = Depends(get_db)
):
    """Submit final KYC for review (Step 4 of KYC)"""
    return submit_final_kyc(church_id, db)
