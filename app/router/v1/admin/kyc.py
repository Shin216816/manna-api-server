from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
from app.controller.admin.kyc import (
    get_kyc_list, get_kyc_details, get_kyc_documents, approve_document, reject_document,
    request_documents, add_document_notes, regenerate_kyc_link, pause_payouts, 
    resume_payouts, add_admin_notes, get_audit_logs, approve_kyc, reject_kyc,
    request_kyc_info, get_kyc_confirmation_queue, get_stripe_account_info
)
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.core.responses import SuccessResponse

kyc_router = APIRouter(tags=["Admin KYC Management"])

@kyc_router.get("/list", response_model=SuccessResponse)
async def get_kyc_list_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    state: Optional[str] = Query(default=None, description="Filter by KYC state"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get list of churches with KYC status for admin review"""
    return get_kyc_list(db, page, limit, state)

@kyc_router.get("/confirmation-queue", response_model=SuccessResponse)
async def get_kyc_confirmation_queue_route(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get churches that need KYC confirmation (in review or needs info)"""
    return get_kyc_confirmation_queue(db, page, limit)

@kyc_router.get("/{church_id}", response_model=SuccessResponse)
async def get_kyc_details_route(
    church_id: int = Path(..., description="Church ID"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get detailed KYC information for a specific church"""
    return get_kyc_details(church_id, db)

@kyc_router.get("/{church_id}/documents", response_model=SuccessResponse)
async def get_kyc_documents_route(
    church_id: int = Path(..., description="Church ID"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get KYC documents for a specific church"""
    return get_kyc_documents(church_id, db)

@kyc_router.get("/{church_id}/stripe", response_model=SuccessResponse)
async def get_stripe_account_info_route(
    church_id: int = Path(..., description="Church ID"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get detailed Stripe account information for a church"""
    return get_stripe_account_info(church_id, db)

@kyc_router.post("/{church_id}/documents/{document_type}/approve", response_model=SuccessResponse)
async def approve_document_route(
    church_id: int = Path(..., description="Church ID"),
    document_type: str = Path(..., description="Document type"),
    data: dict = Body(...),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Approve a specific KYC document"""
    return approve_document(church_id, document_type, current_user["id"], db, data.get("notes"))

@kyc_router.post("/{church_id}/documents/{document_type}/reject", response_model=SuccessResponse)
async def reject_document_route(
    church_id: int = Path(..., description="Church ID"),
    document_type: str = Path(..., description="Document type"),
    data: dict = Body(...),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Reject a specific KYC document"""
    return reject_document(church_id, document_type, current_user["id"], data.get("reason", ""), db, data.get("notes"))

@kyc_router.post("/{church_id}/documents/request", response_model=SuccessResponse)
async def request_documents_route(
    church_id: int = Path(..., description="Church ID"),
    data: dict = Body(...),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Request additional documents from church"""
    return request_documents(church_id, current_user["id"], data.get("required_documents", []), db, data.get("notes"))

@kyc_router.post("/{church_id}/documents/{document_type}/notes", response_model=SuccessResponse)
async def add_document_notes_route(
    church_id: int = Path(..., description="Church ID"),
    document_type: str = Path(..., description="Document type"),
    data: dict = Body(...),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Add notes to a specific document"""
    return add_document_notes(church_id, document_type, current_user["id"], data.get("notes", ""), db)

@kyc_router.post("/{church_id}/approve", response_model=SuccessResponse)
async def approve_kyc_route(
    church_id: int = Path(..., description="Church ID"),
    approval_notes: str = Body(..., embed=True, description="Approval notes"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Approve KYC for a church"""
    return approve_kyc(church_id, current_user["id"], approval_notes, db)

@kyc_router.post("/{church_id}/reject", response_model=SuccessResponse)
async def reject_kyc_route(
    church_id: int = Path(..., description="Church ID"),
    rejection_reason: str = Body(..., embed=True, description="Rejection reason"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Reject KYC for a church"""
    return reject_kyc(church_id, current_user["id"], rejection_reason, db)

@kyc_router.post("/{church_id}/request-info", response_model=SuccessResponse)
async def request_kyc_info_route(
    church_id: int = Path(..., description="Church ID"),
    required_info: str = Body(..., embed=True, description="Required information"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Request additional information for KYC"""
    return request_kyc_info(church_id, current_user["id"], required_info, db)

@kyc_router.post("/{church_id}/regenerate-link", response_model=SuccessResponse)
async def regenerate_kyc_link_route(
    church_id: int = Path(..., description="Church ID"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Regenerate onboarding link for a church"""
    return regenerate_kyc_link(church_id, current_user["id"], db)

@kyc_router.post("/{church_id}/pause-payouts", response_model=SuccessResponse)
async def pause_payouts_route(
    church_id: int = Path(..., description="Church ID"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Pause payouts for a church"""
    return pause_payouts(church_id, current_user["id"], db)

@kyc_router.post("/{church_id}/resume-payouts", response_model=SuccessResponse)
async def resume_payouts_route(
    church_id: int = Path(..., description="Church ID"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Resume payouts for a church"""
    return resume_payouts(church_id, current_user["id"], db)

@kyc_router.post("/{church_id}/notes", response_model=SuccessResponse)
async def add_admin_notes_route(
    church_id: int = Path(..., description="Church ID"),
    notes: str = Body(..., embed=True, description="Admin notes"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Add internal notes for a church"""
    return add_admin_notes(church_id, current_user["id"], notes, db)

@kyc_router.get("/audit/logs", response_model=SuccessResponse)
async def get_audit_logs_route(
    church_id: Optional[int] = Query(default=None, description="Filter by church ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get audit logs for churches"""
    return get_audit_logs(db, church_id, page, limit)
