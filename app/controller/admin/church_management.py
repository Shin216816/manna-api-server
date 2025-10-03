"""
Admin Church Management Controller

Handles admin church management functionality:
- List all churches
- Get church details
- KYC review and approval
- Church status management
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_user import User
from app.schema.admin_schema import ChurchKYCReviewRequest
from app.core.responses import ResponseFactory
from app.utils.audit import log_audit_event
from datetime import datetime, timezone
import logging


def list_churches(status_filter: str, limit: int, offset: int, db: Session):
    """List all churches with filtering"""
    try:
        query = db.query(Church)
        
        # Apply status filter
        if status_filter != "all":
            query = query.filter(Church.status == status_filter)
        
        # Get total count
        total_count = query.count()
        
        # Get churches with pagination
        churches = query.order_by(desc(Church.created_at)).offset(offset).limit(limit).all()
        
        church_data = []
        for church in churches:
            # Get church analytics
            total_revenue_result = db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.church_id == church.id,
                    DonationBatch.status == "success"
                )
            ).scalar()
            total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
            
            # Get active givers count
            active_givers = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
                and_(
                    DonationBatch.church_id == church.id,
                    DonationBatch.status == "success"
                )
            ).scalar()
            
            church_data.append({
                "id": church.id,
                "name": church.name,
                "admin_email": church.email,
                "status": church.status,
                "kyc_status": getattr(church, 'kyc_status', 'not_submitted'),
                "registration_date": church.created_at.isoformat() if church.created_at else None,
                "total_revenue": round(total_revenue, 2),
                "active_givers": active_givers,
                "phone": church.phone,
                "address": church.address
            })
        
        return ResponseFactory.success(
            message="Churches retrieved successfully",
            data={
                "churches": church_data,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        
        return ResponseFactory.error("Error retrieving churches", "500")


def get_church_details(church_id: int, db: Session):
    """Get detailed church information"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        # Get church analytics
        total_revenue_result = db.query(func.sum(DonationBatch.total_amount)).filter(
            and_(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "success"
            )
        ).scalar()
        total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
        
        # Get active givers count
        active_givers = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
            and_(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "success"
            )
        ).scalar()
        
        # Get total donations count
        total_donations = db.query(DonationBatch).filter(
            and_(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "success"
            )
        ).count()
        
        # Get KYC information
        kyc_info = {
            "status": getattr(church, 'kyc_status', 'not_submitted'),
            "submitted_at": church.kyc_submitted_at.isoformat() if hasattr(church, 'kyc_submitted_at') and church.kyc_submitted_at else None,
            "data": getattr(church, 'kyc_data', {})
        }
        
        # Get church analytics
        analytics = {
            "total_revenue": round(total_revenue, 2),
            "active_givers": active_givers,
            "total_donations": total_donations,
            "average_donation": round(total_revenue / total_donations, 2) if total_donations > 0 else 0.0
        }
        
        church_details = {
            "id": church.id,
            "name": church.name,
            "email": church.email,
            "phone": church.phone,
            "address": church.address,
            "ein": church.ein,
            "website": church.website,
            "status": church.status,
            "kyc_info": kyc_info,
            "analytics": analytics,
            "created_at": church.created_at.isoformat() if church.created_at else None,
            "updated_at": church.updated_at.isoformat() if church.updated_at else None
        }
        
        return ResponseFactory.success(
            message="Church details retrieved successfully",
            data={
                "church": church_details
            }
        )
        
    except Exception as e:
        
        return ResponseFactory.error("Error retrieving church details", "500")


def approve_church_kyc(church_id: int, data: ChurchKYCReviewRequest, admin_id: int, db: Session):
    """Approve church KYC"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        if getattr(church, 'kyc_status', 'not_submitted') != 'pending':
            return ResponseFactory.error("Church KYC is not pending review", "400")
        
        # Update church status
        church.kyc_status = "approved"
        church.status = "active"
        church.kyc_approved_at = datetime.now(timezone.utc)
        church.kyc_approved_by = admin_id
        
        db.commit()
        
        # Log audit event
        log_audit_event(
            db=db,
            actor_type="admin",
            actor_id=admin_id,
            action="KYC_APPROVED",
            metadata={
                "resource_type": "church",
                "resource_id": church_id,
                "notes": data.notes
            }
        )
        
        return ResponseFactory.success(
            message="Church KYC approved",
            data={
                "church_id": church_id,
                "approval_date": church.kyc_approved_at.isoformat(),
                "approved_by": admin_id,
                "status": "active"
            }
        )
        
    except Exception as e:
        
        db.rollback()
        return ResponseFactory.error("Error approving KYC", "500")


def reject_church_kyc(church_id: int, data: ChurchKYCReviewRequest, admin_id: int, db: Session):
    """Reject church KYC"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        if getattr(church, 'kyc_status', 'not_submitted') != 'pending':
            return ResponseFactory.error("Church KYC is not pending review", "400")
        
        if not data.reason:
            return ResponseFactory.error("Rejection reason is required", "400")
        
        # Update church status
        church.kyc_status = "rejected"
        church.status = "kyc_rejected"
        church.kyc_rejected_at = datetime.now(timezone.utc)
        church.kyc_rejected_by = admin_id
        church.kyc_rejection_reason = data.reason
        
        db.commit()
        
        # Log audit event
        log_audit_event(
            db=db,
            actor_type="admin",
            actor_id=admin_id,
            action="KYC_REJECTED",
            metadata={
                "resource_type": "church",
                "resource_id": church_id,
                "reason": data.reason,
                "notes": data.notes
            }
        )
        
        return ResponseFactory.success(
            message="Church KYC rejected",
            data={
                "church_id": church_id,
                "rejection_date": church.kyc_rejected_at.isoformat(),
                "rejected_by": admin_id,
                "reason": data.reason,
                "status": "kyc_rejected"
            }
        )
        
    except Exception as e:
        
        db.rollback()
        return ResponseFactory.error("Error rejecting KYC", "500") 
