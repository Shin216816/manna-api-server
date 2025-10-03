from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.core.responses import ResponseFactory
from app.schema.church_schema import ChurchProfileUpdateRequest
from app.services.church_notification_service import ChurchNotificationService


def get_all_churches(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get all churches with pagination and filtering"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        query = db.query(Church)

        if status and status != "all":
            query = query.filter(Church.status == status)

        total = query.count()
        churches = query.offset(offset).limit(limit).all()

        churches_data = []
        for church in churches:
            # Get church admin
            admin = db.query(ChurchAdmin).filter_by(church_id=church.id).first()

            # Get member count
            member_count = (
                db.query(func.count(User.id)).filter_by(church_id=church.id).scalar()
            )

            # Get total donations
            total_donations = (
                db.query(func.sum(DonationBatch.total_amount))
                .filter(
                    DonationBatch.church_id == church.id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0.0
            )

            churches_data.append(
                {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "phone": church.phone,
                    "website": church.website,
                    "status": church.status,
                    "is_active": church.is_active,
                    "kyc_status": church.kyc_status,
                    "created_at": (
                        church.created_at.isoformat() if church.created_at else None
                    ),
                    "admin": {
                        "id": admin.id if admin else None,
                        "email": admin.user.email if admin and admin.user else None,
                        "name": (
                            f"{admin.user.first_name} {admin.user.last_name}"
                            if admin and admin.user
                            else None
                        ),
                    },
                    "stats": {
                        "member_count": member_count,
                        "total_donations": round(float(total_donations or 0), 2),
                    },
                }
            )

        return ResponseFactory.success(
            message="Churches retrieved successfully",
            data={
                "churches": churches_data,
                "pagination": {
                    "page": (offset // limit) + 1 if limit > 0 else 1,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if limit > 0 else 1,
                },
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve churches")


def get_church_details(church_id: int, db: Session):
    """Get detailed church information"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get church admin
        admin = db.query(ChurchAdmin).filter_by(church_id=church.id).first()

        # Get member count
        member_count = (
            db.query(func.count(User.id)).filter_by(church_id=church.id).scalar()
        )

        # Get total donations
        total_donations = (
            db.query(func.sum(DonationBatch.amount))
            .filter(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "completed",
            )
            .scalar()
            or 0.0
        )

        # Get this month's donations
        current_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        this_month_donations = (
            db.query(func.sum(DonationBatch.amount))
            .filter(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_month,
            )
            .scalar()
            or 0.0
        )

        # Get active donors count
        active_donors = (
            db.query(func.count(User.id.distinct()))
            .join(DonationPreference)
            .filter(User.church_id == church.id, DonationPreference.pause == False)
            .scalar()
        )

        return ResponseFactory.success(
            message="Church details retrieved successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "phone": church.phone,
                    "website": church.website,
                    "address": church.address,
                    "city": church.city,
                    "state": church.state,
                    "zip_code": church.zip_code,
                    "status": church.status,
                    "is_active": church.is_active,
                    "kyc_status": church.kyc_status,
                    "stripe_account_id": church.stripe_account_id,
                    "referral_code": church.referral_code,
                    "created_at": (
                        church.created_at.isoformat() if church.created_at else None
                    ),
                    "updated_at": (
                        church.updated_at.isoformat() if church.updated_at else None
                    ),
                },
                "admin": {
                    "id": admin.id if admin else None,
                    "email": admin.user.email if admin and admin.user else None,
                    "first_name": (
                        admin.user.first_name if admin and admin.user else None
                    ),
                    "last_name": admin.user.last_name if admin and admin.user else None,
                    "phone": admin.user.phone if admin and admin.user else None,
                },
                "stats": {
                    "member_count": member_count,
                    "active_donors": active_donors,
                    "total_donations": round(float(total_donations or 0), 2),
                    "this_month_donations": round(float(this_month_donations), 2),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve church details")


def update_church_status(church_id: int, is_active: bool, db: Session):
    """Update church status"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        church.is_active = is_active
        church.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Church status updated successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "is_active": church.is_active,
                    "updated_at": church.updated_at.isoformat(),
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update church status")


def approve_church_kyc(church_id: int, data, db: Session):
    """Approve church KYC"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        church.kyc_status = "approved"
        church.status = "active"
        church.is_active = True
        church.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Church KYC approved successfully",
            data={
                "church_id": church.id,
                "kyc_status": church.kyc_status,
                "status": church.status,
                "is_active": church.is_active,
                "updated_at": church.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to approve church KYC")


def reject_church_kyc(church_id: int, data, db: Session):
    """Reject church KYC"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Update KYC status to rejected
        church.kyc_status = "rejected"
        church.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Church KYC rejected successfully",
            data={
                "church_id": church.id,
                "kyc_status": church.kyc_status,
                "rejection_reason": getattr(data, "reason", "No reason provided"),
                "updated_at": church.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reject church KYC")


def get_church_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get church analytics"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Build query for donations
        query = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id, DonationBatch.status == "completed"
        )

        if start_date:
            query = query.filter(DonationBatch.created_at >= start_date)
        if end_date:
            query = query.filter(DonationBatch.created_at <= end_date)

        donations = query.all()

        # Calculate analytics
        total_amount = sum(float(d.total_amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_amount / donation_count if donation_count > 0 else 0.0

        # Monthly breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.total_amount)
            monthly_data[month_key]["count"] += 1

        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        return ResponseFactory.success(
            message="Church analytics retrieved successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "analytics": {
                    "total_amount": round(float(total_amount), 2),
                    "donation_count": donation_count,
                    "average_donation": round(float(avg_donation), 2),
                },
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for month, data in sorted_monthly
                ],
                "date_range": {"start_date": start_date, "end_date": end_date},
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve church analytics"
        )


def get_church_members(
    church_id: int, page: int = 1, limit: int = 20, db: Optional[Session] = None
):
    """Get church members"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        query = db.query(User).filter_by(church_id=church_id)
        total = query.count()
        members = query.offset((page - 1) * limit).limit(limit).all()

        members_data = []
        for member in members:
            # Get member's total donations
            total_donations = (
                db.query(func.sum(DonationBatch.amount))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0.0
            )

            # Get member's donation count
            donation_count = (
                db.query(func.count(DonationBatch.id))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0
            )

            # Get member's last donation date
            last_donation = (
                db.query(DonationBatch.created_at)
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .order_by(DonationBatch.created_at.desc())
                .first()
            )

            # Get member's donation preferences
            preferences = (
                db.query(DonationPreference)
                .filter(DonationPreference.user_id == member.id)
                .first()
            )

            # Calculate average donation
            avg_donation = 0.0
            if donation_count > 0:
                avg_donation = float(total_donations) / donation_count

            members_data.append(
                {
                    "id": member.id,
                    "email": member.email,
                    "phone": member.phone,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "is_active": member.is_active,
                    "is_email_verified": member.is_email_verified,
                    "is_phone_verified": member.is_phone_verified,
                    "created_at": (
                        member.created_at.isoformat() if member.created_at else None
                    ),
                    "last_login": (
                        member.last_login.isoformat() if member.last_login else None
                    ),
                    "total_donations": round(float(total_donations or 0), 2),
                    "donation_count": donation_count,
                    "average_donation": round(avg_donation, 2),
                    "last_donation": (
                        last_donation[0].isoformat() if last_donation and last_donation[0] else None
                    ),
                    "roundup_enabled": not preferences.pause if preferences else False,
                    "donation_frequency": (
                        preferences.frequency if preferences else None
                    ),
                    "role": member.role,
                    "status": "active" if member.is_active else "inactive"
                }
            )

        return ResponseFactory.success(
            message="Church members retrieved successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "phone": church.phone,
                    "address": church.address,
                    "city": church.city,
                    "state": church.state,
                    "zip_code": church.zip_code,
                    "country": church.country,
                },
                "members": members_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
                "summary": {
                    "total_members": total,
                    "active_members": len([m for m in members_data if m["is_active"]]),
                    "total_donations": round(sum(m["total_donations"] for m in members_data), 2),
                    "average_donation": round(
                        sum(m["total_donations"] for m in members_data) / len(members_data) 
                        if members_data else 0, 2
                    ),
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve church members")


def get_church_donations(
    church_id: int, page: int = 1, limit: int = 20, db: Optional[Session] = None
):
    """Get church donations with comprehensive data"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get all completed donations for this church
        query = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id, 
            DonationBatch.status == "completed"
        )
        total = query.count()
        donations = (
            query.order_by(DonationBatch.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        donations_data = []
        for donation in donations:
            # Get donor information
            donor = db.query(User).filter(User.id == donation.user_id).first()
            
            # Get donation preferences for this donor
            preferences = (
                db.query(DonationPreference)
                .filter(DonationPreference.user_id == donation.user_id)
                .first()
            )

            donations_data.append(
                {
                    "id": donation.id,
                    "user_id": donation.user_id,
                    "amount": float(donation.amount),
                    "transaction_count": donation.transaction_count or 0,
                    "status": donation.status,
                    "type": "roundup",  # All DonationBatch entries are roundup donations
                    "processing_fee": float(donation.processing_fee) if donation.processing_fee else 0.0,
                    "net_amount": float(donation.net_amount) if donation.net_amount else 0.0,
                    "batch_number": donation.batch_number,
                    "created_at": donation.created_at.isoformat(),
                    "collection_date": (
                        donation.collection_date.isoformat() 
                        if donation.collection_date else None
                    ),
                    "payout_date": (
                        donation.payout_date.isoformat() 
                        if donation.payout_date else None
                    ),
                    "updated_at": (
                        donation.updated_at.isoformat()
                        if donation.updated_at
                        else None
                    ),
                    "stripe_transfer_id": donation.stripe_transfer_id,
                    "donor": {
                        "id": donor.id if donor else None,
                        "first_name": donor.first_name if donor else "Unknown",
                        "last_name": donor.last_name if donor else "Donor",
                        "email": donor.email if donor else None,
                        "phone": donor.phone if donor else None,
                        "is_active": donor.is_active if donor else False,
                    },
                    "preferences": {
                        "roundup_enabled": not preferences.pause if preferences else False,
                        "frequency": preferences.frequency if preferences else None,
                        "multiplier": preferences.multiplier if preferences else 1.0,
                    }
                }
            )

        # Calculate summary statistics
        total_amount = sum(float(d.amount) for d in donations)
        avg_donation = total_amount / len(donations) if donations else 0.0
        total_transactions = sum(d.transaction_count or 0 for d in donations)
        
        # Get unique donors count
        unique_donors = len(set(d.user_id for d in donations))
        
        # Get recent activity (last 30 days)
        from datetime import datetime, timezone, timedelta
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_donations = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= thirty_days_ago
        ).count()
        
        recent_amount = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= thirty_days_ago
        ).scalar() or 0.0

        return ResponseFactory.success(
            message="Church donations retrieved successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "phone": church.phone,
                    "address": church.address,
                    "city": church.city,
                    "state": church.state,
                    "zip_code": church.zip_code,
                    "country": church.country,
                },
                "donations": donations_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
                "summary": {
                    "total_donations": total,
                    "total_amount": round(total_amount, 2),
                    "average_donation": round(avg_donation, 2),
                    "total_transactions": total_transactions,
                    "unique_donors": unique_donors,
                    "recent_donations_30d": recent_donations,
                    "recent_amount_30d": round(float(recent_amount), 2),
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve church donations: {str(e)}"
        )


def get_church_kyc_details(
    church_id: int, db: Optional[Session] = None
):
    """Get comprehensive church KYC details for admin"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Parse KYC data from JSON field
        import json
        if church.kyc_data:
            if isinstance(church.kyc_data, str):
                try:
                    kyc_data = json.loads(church.kyc_data)
                except (json.JSONDecodeError, TypeError):
                    kyc_data = {}
            else:
                kyc_data = church.kyc_data
        else:
            kyc_data = {}
        
        # Get audit logs for this church
        from app.model.m_audit_log import AuditLog
        audit_logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "church",
                AuditLog.resource_id == church_id
            )
            .order_by(AuditLog.created_at.desc())
            .limit(50)
            .all()
        )

        # Format audit logs
        formatted_logs = []
        for log in audit_logs:
            formatted_logs.append({
                "id": log.id,
                "action": log.action,
                "actor_type": log.actor_type,
                "actor_id": log.actor_id,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "additional_data": log.additional_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
            })

        # Get document status from KYC data
        documents_status = {}
        if kyc_data.get("documents"):
            for doc_type, doc_info in kyc_data["documents"].items():
                documents_status[doc_type] = {
                    "status": doc_info.get("status", "not_uploaded"),
                    "uploaded_at": doc_info.get("uploaded_at"),
                    "file_path": doc_info.get("file_path"),
                    "file_name": doc_info.get("file_name"),
                    "file_size": doc_info.get("file_size"),
                    "notes": doc_info.get("notes"),
                }

        # Get control persons from KYC data
        control_persons = kyc_data.get("control_persons", [])

        # Calculate KYC completion percentage
        required_fields = [
            "legal_name", "ein", "website", "phone", "email", "address", 
            "city", "state", "zip_code", "country", "primary_purpose"
        ]
        completed_fields = sum(1 for field in required_fields if kyc_data.get(field))
        completion_percentage = (completed_fields / len(required_fields)) * 100

        # Get document completion
        required_documents = [
            "articles_of_incorporation", "tax_exempt_letter", 
            "bank_statement", "board_resolution"
        ]
        uploaded_documents = sum(1 for doc in required_documents if documents_status.get(doc, {}).get("status") == "uploaded")
        document_completion = (uploaded_documents / len(required_documents)) * 100

        return ResponseFactory.success(
            message="Church KYC details retrieved successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "legal_name": church.legal_name,
                    "email": church.email,
                    "phone": church.phone,
                    "address": church.address,
                    "city": church.city,
                    "state": church.state,
                    "zip_code": church.zip_code,
                    "country": church.country,
                    "website": church.website,
                    "ein": church.ein,
                    "primary_purpose": church.primary_purpose,
                    "kyc_status": church.kyc_status,
                    "kyc_state": church.kyc_state,
                    "created_at": church.created_at.isoformat() if church.created_at else None,
                    "updated_at": church.updated_at.isoformat() if church.updated_at else None,
                },
                "kyc_data": {
                    "legal_information": {
                        "legal_name": kyc_data.get("legal_name"),
                        "ein": kyc_data.get("ein"),
                        "website": kyc_data.get("website"),
                        "phone": kyc_data.get("phone"),
                        "email": kyc_data.get("email"),
                        "address": kyc_data.get("address"),
                        "address_line_2": kyc_data.get("address_line_2"),
                        "city": kyc_data.get("city"),
                        "state": kyc_data.get("state"),
                        "zip_code": kyc_data.get("zip_code"),
                        "country": kyc_data.get("country"),
                        "primary_purpose": kyc_data.get("primary_purpose"),
                        "formation_date": kyc_data.get("formation_date"),
                        "formation_state": kyc_data.get("formation_state"),
                    },
                    "control_persons": control_persons,
                    "documents": documents_status,
                    "compliance_attestations": {
                        "tax_exempt": kyc_data.get("tax_exempt", False),
                        "anti_terrorism": kyc_data.get("anti_terrorism", False),
                        "legitimate_entity": kyc_data.get("legitimate_entity", False),
                    },
                    "completion_status": {
                        "overall_percentage": round(completion_percentage, 2),
                        "document_percentage": round(document_completion, 2),
                        "completed_fields": completed_fields,
                        "total_fields": len(required_fields),
                        "uploaded_documents": uploaded_documents,
                        "total_documents": len(required_documents),
                    }
                },
                "stripe_information": {
                    "stripe_account_id": church.stripe_account_id,
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                },
                "audit_logs": formatted_logs,
                "submission_info": {
                    "submitted_at": kyc_data.get("submitted_at"),
                    "last_updated": kyc_data.get("last_updated"),
                    "submission_id": kyc_data.get("submission_id"),
                    "review_notes": kyc_data.get("review_notes"),
                    "admin_notes": kyc_data.get("admin_notes"),
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve church KYC details: {str(e)}"
        )


def update_church_profile_admin(church_id: int, update_data: ChurchProfileUpdateRequest, admin_id: int, admin_name: str, db: Session):
    """Update church profile (admin only)"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Store old values for audit
        old_values = {
            "name": church.name,
            "website": church.website,
            "phone": church.phone,
            "email": church.email,
            "address": church.address,
            "city": church.city,
            "state": church.state,
            "zip_code": church.zip_code,
            "country": church.country,
        }

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        changed_fields = []
        new_values = {}
        
        for field, value in update_dict.items():
            if hasattr(church, field):
                old_value = getattr(church, field)
                if old_value != value:  # Only track actually changed fields
                    changed_fields.append(field)
                    new_values[field] = value
                setattr(church, field, value)

        church.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(church)

        # Send notifications if there were actual changes
        notification_result = None
        if changed_fields:
            try:
                notification_service = ChurchNotificationService(db)
                notification_result = notification_service.send_church_data_change_notification(
                    church_id=church_id,
                    admin_id=admin_id,
                    changed_fields=changed_fields,
                    old_values=old_values,
                    new_values=new_values,
                    admin_name=admin_name
                )
            except Exception as e:
                # Log notification error but don't fail the update
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send church change notifications: {str(e)}")

        response_data = {
            "id": church.id,
            "name": church.name,
            "website": church.website,
            "phone": church.phone,
            "email": church.email,
            "address": church.address,
            "city": church.city,
            "state": church.state,
            "zip_code": church.zip_code,
            "country": church.country,
            "updated_at": church.updated_at.isoformat(),
            "updated_fields": changed_fields,
        }
        
        # Include notification results if available
        if notification_result:
            response_data["notifications"] = {
                "sent": notification_result.get("success", False),
                "message": notification_result.get("message", ""),
                "emails_sent": notification_result.get("data", {}).get("emails_sent", 0),
                "total_admins": notification_result.get("data", {}).get("total_admins", 0)
            }

        return ResponseFactory.success(
            message="Church profile updated successfully",
            data=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to update church profile"
        )


def get_church_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get comprehensive church analytics for admin"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    
    try:
        # Get church information
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Parse dates
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = datetime.now(timezone.utc) - timedelta(days=30)  # Default 30 days

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = datetime.now(timezone.utc)

        # Get donation data from DonationBatch
        donation_query = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed"
        ).filter(
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        )

        donations = donation_query.all()

        # Calculate basic metrics
        total_donations = sum(float(d.amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_donations / donation_count if donation_count > 0 else 0.0
        total_transactions = sum(d.transaction_count for d in donations)

        # Get unique donors
        unique_donors = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).scalar() or 0

        # Get church members count
        total_members = db.query(User).filter(User.church_id == church_id).count()

        # Monthly breakdown
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0, "transactions": 0}
            monthly_data[month_key]["amount"] += float(donation.amount)
            monthly_data[month_key]["count"] += 1
            monthly_data[month_key]["transactions"] += donation.transaction_count

        # Sort monthly data
        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        # Daily breakdown for the last 30 days
        daily_data = {}
        for donation in donations:
            day_key = donation.created_at.strftime("%Y-%m-%d")
            if day_key not in daily_data:
                daily_data[day_key] = {"amount": 0.0, "count": 0}
            daily_data[day_key]["amount"] += float(donation.amount)
            daily_data[day_key]["count"] += 1

        # Sort daily data
        sorted_daily = sorted(daily_data.items(), key=lambda x: x[0])

        # Get previous period for comparison
        period_days = (end_dt - start_dt).days
        prev_start_dt = start_dt - timedelta(days=period_days)
        prev_end_dt = start_dt

        prev_donations = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed"
        ).filter(
            DonationBatch.created_at >= prev_start_dt,
            DonationBatch.created_at < prev_end_dt
        ).all()

        prev_total_donations = sum(float(d.amount) for d in prev_donations)
        prev_donation_count = len(prev_donations)

        # Calculate growth percentages
        donation_growth = 0.0
        if prev_total_donations > 0:
            donation_growth = ((total_donations - prev_total_donations) / prev_total_donations) * 100

        count_growth = 0.0
        if prev_donation_count > 0:
            count_growth = ((donation_count - prev_donation_count) / prev_donation_count) * 100

        # Get church payouts
        church_payouts = db.query(ChurchPayout).filter(
            ChurchPayout.church_id == church_id,
            ChurchPayout.status == "completed"
        ).filter(
            ChurchPayout.created_at >= start_dt,
            ChurchPayout.created_at <= end_dt
        ).all()

        total_payouts = sum(float(p.amount) for p in church_payouts)

        # Prepare analytics data
        analytics_data = {
            "church": {
                "id": church.id,
                "name": church.name,
                "email": church.email,
                "phone": church.phone,
                "address": church.address,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
                "country": church.country,
                "kyc_status": church.kyc_status,
                "is_active": church.is_active,
                "created_at": church.created_at.isoformat() if church.created_at else None,
            },
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "days": period_days
            },
            "overview": {
                "total_donations": round(total_donations, 2),
                "donation_count": donation_count,
                "average_donation": round(avg_donation, 2),
                "total_transactions": total_transactions,
                "unique_donors": unique_donors,
                "total_members": total_members,
                "total_payouts": round(total_payouts, 2),
                "net_revenue": round(total_donations - total_payouts, 2)
            },
            "growth": {
                "donation_growth_percent": round(donation_growth, 2),
                "count_growth_percent": round(count_growth, 2),
                "previous_period_donations": round(prev_total_donations, 2),
                "previous_period_count": prev_donation_count
            },
            "breakdowns": {
                "monthly": [{"month": month, "amount": data["amount"], "count": data["count"], "transactions": data["transactions"]} 
                           for month, data in sorted_monthly],
                "daily": [{"date": day, "amount": data["amount"], "count": data["count"]} 
                         for day, data in sorted_daily[-30:]]  # Last 30 days
            },
            "recent_donations": [
                {
                    "id": d.id,
                    "user_id": d.user_id,
                    "amount": float(d.amount),
                    "transaction_count": d.transaction_count,
                    "status": d.status,
                    "created_at": d.created_at.isoformat(),
                    "processed_at": d.processed_at.isoformat() if d.processed_at else None
                }
                for d in donations[-10:]  # Last 10 donations
            ]
        }

        return ResponseFactory.success(
            message="Church analytics retrieved successfully",
            data=analytics_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve church analytics: {str(e)}"
        )
