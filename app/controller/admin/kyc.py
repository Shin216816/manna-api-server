from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.model.m_church import Church
from app.model.m_audit_log import AuditLog
from app.services.kyc_service import KYCService
from app.services.notification_service import NotificationService
from app.core.responses import ResponseFactory, SuccessResponse
from app.core.exceptions import StripeError
import json
import uuid
from typing import Optional


def get_kyc_list(
    db: Session, page: int = 1, limit: int = 20, state: Optional[str] = None
) -> SuccessResponse:
    """Get list of churches with KYC status for admin review"""
    try:
        query = db.query(Church)

        # Filter by KYC state if provided
        if state:
            query = query.filter(Church.kyc_state == state)

        # Pagination
        total = query.count()
        churches = query.offset((page - 1) * limit).limit(limit).all()

        # Format response data
        church_data = []
        for church in churches:
            church_data.append(
                {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "kyc_state": church.kyc_state,
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                    "disabled_reason": church.disabled_reason,
                    "stripe_account_id": church.stripe_account_id,
                    "created_at": church.created_at,
                    "updated_at": church.updated_at,
                    "verified_at": church.verified_at,
                    "requirements_count": 0,  # Using existing kyc_data instead
                }
            )

        return ResponseFactory.success(
            message="KYC list retrieved successfully",
            data={
                "churches": church_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get KYC list")


def get_kyc_details(church_id: int, db: Session) -> SuccessResponse:
    """Get detailed KYC information for a specific church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Sync with Stripe to get latest status
        try:
            status_data = KYCService.sync_stripe_account_status(church, db)
        except StripeError:
            # Use cached data if Stripe sync fails
            status_data = {
                "kyc_state": church.kyc_state,
                "charges_enabled": church.charges_enabled,
                "payouts_enabled": church.payouts_enabled,
                "disabled_reason": church.disabled_reason,
            }

        # Get beneficial owners
        from app.model.m_beneficial_owner import BeneficialOwner
        beneficial_owners = db.query(BeneficialOwner).filter(
            BeneficialOwner.church_id == church_id
        ).all()

        # Get church admin
        from app.model.m_church_admin import ChurchAdmin
        church_admin = db.query(ChurchAdmin).filter(
            ChurchAdmin.church_id == church_id
        ).first()

        # Get recent audit logs
        audit_logs = (
            db.query(AuditLog)
            .filter(AuditLog.church_id == church_id)
            .order_by(AuditLog.created_at.desc())
            .limit(20)
            .all()
        )

        audit_data = []
        for log in audit_logs:
            audit_data.append(
                {
                    "id": log.id,
                    "actor_type": log.actor_type,
                    "actor_id": log.actor_id,
                    "action": log.action,
                    "details": log.details_json,
                    "created_at": log.created_at,
                }
            )

        # Build comprehensive KYC data structure
        kyc_data = {
            "legal_information": {
                "legal_name": church.legal_name or church.name,
                "ein": church.ein,
                "website": church.website,
                "phone": church.phone,
                "email": church.email,
                "address": church.address_line_1 or church.address,
                "address_line_2": church.address_line_2,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
                "country": church.country or "US",
                "primary_purpose": church.primary_purpose,
                "formation_date": church.formation_date.isoformat() if church.formation_date else None,
                "formation_state": church.formation_state,
            },
            "control_persons": [
                {
                    "first_name": owner.first_name,
                    "last_name": owner.last_name,
                    "title": owner.title,
                    "email": owner.email,
                    "phone": owner.phone,
                    "date_of_birth": owner.date_of_birth.isoformat() if owner.date_of_birth else None,
                    "ssn": owner.ssn_full,
                    "address": owner.address_line_1,
                    "city": owner.city,
                    "state": owner.state,
                    "zip_code": owner.zip_code,
                    "country_of_residence": owner.country,
                }
                for owner in beneficial_owners
            ],
            "documents": {
                "articles_of_incorporation": {
                    "status": "uploaded" if church.articles_of_incorporation else "not_uploaded",
                    "uploaded_at": church.updated_at.isoformat() if church.articles_of_incorporation else None,
                    "file_path": church.articles_of_incorporation,
                    "file_name": "Articles of Incorporation" if church.articles_of_incorporation else None,
                    "file_size": 0,  # Would need to calculate from file
                    "notes": "",
                },
                "tax_exempt_letter": {
                    "status": "uploaded" if church.tax_exempt_letter else "not_uploaded",
                    "uploaded_at": church.updated_at.isoformat() if church.tax_exempt_letter else None,
                    "file_path": church.tax_exempt_letter,
                    "file_name": "IRS Tax Exempt Letter" if church.tax_exempt_letter else None,
                    "file_size": 0,
                    "notes": "",
                },
                "bank_statement": {
                    "status": "uploaded" if church.bank_statement else "not_uploaded",
                    "uploaded_at": church.updated_at.isoformat() if church.bank_statement else None,
                    "file_path": church.bank_statement,
                    "file_name": "Bank Statement" if church.bank_statement else None,
                    "file_size": 0,
                    "notes": "",
                },
                "board_resolution": {
                    "status": "uploaded" if church.board_resolution else "not_uploaded",
                    "uploaded_at": church.updated_at.isoformat() if church.board_resolution else None,
                    "file_path": church.board_resolution,
                    "file_name": "Board Resolution" if church.board_resolution else None,
                    "file_size": 0,
                    "notes": "",
                },
            },
            "compliance_attestations": {
                "tax_exempt": church.tax_exempt,
                "anti_terrorism": church.anti_terrorism,
                "legitimate_entity": church.legitimate_entity,
                "consent_checks": church.consent_checks,
                "beneficial_ownership_disclosure": church.beneficial_ownership_disclosure,
                "information_accuracy": church.information_accuracy,
                "penalty_of_perjury": church.penalty_of_perjury,
            },
            "completion_status": {
                "overall_percentage": _calculate_kyc_completion_percentage(church, beneficial_owners),
                "document_percentage": _calculate_document_completion_percentage(church),
                "completed_fields": _count_completed_fields(church, beneficial_owners),
                "total_fields": _count_total_fields(),
                "uploaded_documents": _count_uploaded_documents(church),
                "total_documents": 4,  # Fixed number of required documents
            },
        }

        return ResponseFactory.success(
            message="KYC details retrieved successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "legal_name": church.legal_name,
                    "email": church.email,
                    "phone": church.phone,
                    "website": church.website,
                    "address": church.address_line_1 or church.address,
                    "city": church.city,
                    "state": church.state,
                    "zip_code": church.zip_code,
                    "country": church.country,
                    "ein": church.ein,
                    "primary_purpose": church.primary_purpose,
                    "kyc_status": church.kyc_status,
                    "kyc_state": church.kyc_state,
                    "created_at": church.created_at.isoformat() if church.created_at else None,
                    "updated_at": church.updated_at.isoformat() if church.updated_at else None,
                },
                "kyc_data": kyc_data,
                "stripe_information": {
                    "stripe_account_id": church.stripe_account_id,
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                    "disabled_reason": church.disabled_reason,
                },
                "audit_logs": audit_data,
                "submission_info": {
                    "submitted_at": church.kyc_submitted_at.isoformat() if church.kyc_submitted_at else None,
                    "last_updated": church.updated_at.isoformat() if church.updated_at else None,
                    "submission_id": f"KYC-{church.id}-{church.created_at.strftime('%Y%m%d')}" if church.created_at else None,
                    "review_notes": church.kyc_data.get("review_notes", "") if church.kyc_data else "",
                    "admin_notes": church.kyc_data.get("admin_notes", "") if church.kyc_data else "",
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get KYC details")


def _calculate_kyc_completion_percentage(church: Church, beneficial_owners: list) -> int:
    """Calculate overall KYC completion percentage"""
    total_fields = 0
    completed_fields = 0
    
    # Church information fields
    church_fields = [
        church.legal_name or church.name,
        church.ein,
        church.phone,
        church.email,
        church.address_line_1 or church.address,
        church.city,
        church.state,
        church.zip_code,
        church.primary_purpose,
    ]
    total_fields += len(church_fields)
    completed_fields += sum(1 for field in church_fields if field)
    
    # Document fields
    doc_fields = [
        church.articles_of_incorporation,
        church.tax_exempt_letter,
        church.bank_statement,
        church.board_resolution,
    ]
    total_fields += len(doc_fields)
    completed_fields += sum(1 for field in doc_fields if field)
    
    # Beneficial owner fields
    for owner in beneficial_owners:
        owner_fields = [
            owner.first_name,
            owner.last_name,
            owner.email,
            owner.date_of_birth,
            owner.ssn,
            owner.address_line_1,
        ]
        total_fields += len(owner_fields)
        completed_fields += sum(1 for field in owner_fields if field)
    
    return int((completed_fields / total_fields * 100)) if total_fields > 0 else 0


def _calculate_document_completion_percentage(church: Church) -> int:
    """Calculate document completion percentage"""
    doc_fields = [
        church.articles_of_incorporation,
        church.tax_exempt_letter,
        church.bank_statement,
        church.board_resolution,
    ]
    completed = sum(1 for field in doc_fields if field)
    return int((completed / len(doc_fields) * 100))


def _count_completed_fields(church: Church, beneficial_owners: list) -> int:
    """Count completed fields"""
    completed = 0
    
    # Church fields
    church_fields = [
        church.legal_name or church.name,
        church.ein,
        church.phone,
        church.email,
        church.address_line_1 or church.address,
        church.city,
        church.state,
        church.zip_code,
        church.primary_purpose,
    ]
    completed += sum(1 for field in church_fields if field)
    
    # Document fields
    doc_fields = [
        church.articles_of_incorporation,
        church.tax_exempt_letter,
        church.bank_statement,
        church.board_resolution,
    ]
    completed += sum(1 for field in doc_fields if field)
    
    # Beneficial owner fields
    for owner in beneficial_owners:
        owner_fields = [
            owner.first_name,
            owner.last_name,
            owner.email,
            owner.date_of_birth,
            owner.ssn,
            owner.address_line_1,
        ]
        completed += sum(1 for field in owner_fields if field)
    
    return completed


def _count_total_fields() -> int:
    """Count total required fields"""
    return 9 + 4 + 6  # Church fields + Document fields + Per beneficial owner fields


def _count_uploaded_documents(church: Church) -> int:
    """Count uploaded documents"""
    doc_fields = [
        church.articles_of_incorporation,
        church.tax_exempt_letter,
        church.bank_statement,
        church.board_resolution,
    ]
    return sum(1 for field in doc_fields if field)


def get_stripe_account_info(church_id: int, db: Session) -> SuccessResponse:
    """Get detailed Stripe account information for a church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if not church.stripe_account_id:
            return ResponseFactory.success(
                message="No Stripe account found",
                data={
                    "stripe_account_id": None,
                    "account_status": "not_created",
                    "message": "Stripe Connect account has not been created yet",
                },
            )

        try:
            # Get account details from Stripe
            from app.services.stripe_service import get_account

            account_data = get_account(church.stripe_account_id)

            # Get account requirements
            requirements = account_data.get("requirements", {})
            currently_due = requirements.get("currently_due", [])
            eventually_due = requirements.get("eventually_due", [])
            past_due = requirements.get("past_due", [])

            return ResponseFactory.success(
                message="Stripe account information retrieved successfully",
                data={
                    "stripe_account_id": church.stripe_account_id,
                    "account_status": account_data.get("charges_enabled")
                    and account_data.get("payouts_enabled"),
                    "charges_enabled": account_data.get("charges_enabled", False),
                    "payouts_enabled": account_data.get("payouts_enabled", False),
                    "details_submitted": account_data.get("details_submitted", False),
                    "disabled": account_data.get("disabled", False),
                    "disabled_reason": account_data.get("disabled_reason"),
                    "business_type": account_data.get("business_type"),
                    "country": account_data.get("country"),
                    "created": account_data.get("created"),
                    "requirements": {
                        "currently_due": currently_due,
                        "eventually_due": eventually_due,
                        "past_due": past_due,
                        "disabled_reason": requirements.get("disabled_reason"),
                    },
                    "business_profile": account_data.get("business_profile", {}),
                    "capabilities": account_data.get("capabilities", {}),
                },
            )

        except Exception as e:
            return ResponseFactory.success(
                message="Stripe account information retrieved with cached data",
                data={
                    "stripe_account_id": church.stripe_account_id,
                    "account_status": church.charges_enabled and church.payouts_enabled,
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                    "disabled_reason": church.disabled_reason,
                    "message": "Using cached data due to Stripe API error",
                    "error": str(e),
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to get Stripe account information"
        )


def get_kyc_documents(church_id: int, db: Session) -> SuccessResponse:
    """Get KYC documents for a specific church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Parse documents JSON if it exists (from Church model)
        documents = {}
        if church.documents:
            try:
                documents = json.loads(church.documents)
            except json.JSONDecodeError:
                documents = {}

        # Build document list
        document_list = []

        # Parse document status from Church model
        document_status = {}
        if church.document_status:
            if isinstance(church.document_status, dict):
                document_status = church.document_status
            elif isinstance(church.document_status, str):
                try:
                    document_status = json.loads(church.document_status)
                except json.JSONDecodeError:

                    document_status = {}
            else:
                document_status = {}

        # Parse document notes from Church model
        document_notes = {}
        if church.document_notes:
            if isinstance(church.document_notes, dict):
                document_notes = church.document_notes
            elif isinstance(church.document_notes, str):
                try:
                    document_notes = json.loads(church.document_notes)
                except json.JSONDecodeError:

                    document_notes = {}
            else:
                document_notes = {}

        # Add documents from Church model (consolidated from ChurchKYC)
        if church.articles_of_incorporation_url:
            doc_status = document_status.get("articles_of_incorporation", {}).get(
                "status", "pending"
            )
            doc_notes = document_notes.get("articles_of_incorporation", {}).get("notes")
            document_list.append(
                {
                    "type": "articles_of_incorporation",
                    "name": "Articles of Incorporation",
                    "url": church.articles_of_incorporation_url,
                    "uploaded_at": (
                        church.updated_at.isoformat() if church.updated_at else None
                    ),
                    "status": doc_status,
                    "notes": doc_notes,
                }
            )

        if church.irs_letter_url:
            doc_status = document_status.get("tax_exempt_letter", {}).get(
                "status", "pending"
            )
            doc_notes = document_notes.get("tax_exempt_letter", {}).get("notes")
            document_list.append(
                {
                    "type": "tax_exempt_letter",
                    "name": "IRS Tax Exempt Letter",
                    "url": church.irs_letter_url,
                    "uploaded_at": (
                        church.updated_at.isoformat() if church.updated_at else None
                    ),
                    "status": doc_status,
                    "notes": doc_notes,
                }
            )

        if church.bank_statement_url:
            doc_status = document_status.get("bank_statement", {}).get(
                "status", "pending"
            )
            doc_notes = document_notes.get("bank_statement", {}).get("notes")
            document_list.append(
                {
                    "type": "bank_statement",
                    "name": "Bank Statement",
                    "url": church.bank_statement_url,
                    "uploaded_at": (
                        church.updated_at.isoformat() if church.updated_at else None
                    ),
                    "status": doc_status,
                    "notes": doc_notes,
                }
            )

        if church.board_resolution_url:
            doc_status = document_status.get("board_resolution", {}).get(
                "status", "pending"
            )
            doc_notes = document_notes.get("board_resolution", {}).get("notes")
            document_list.append(
                {
                    "type": "board_resolution",
                    "name": "Board Resolution",
                    "url": church.board_resolution_url,
                    "uploaded_at": (
                        church.updated_at.isoformat() if church.updated_at else None
                    ),
                    "status": doc_status,
                    "notes": doc_notes,
                }
            )

        # Add documents from Church model JSON field (legacy)
        for doc_type, doc_data in documents.items():
            if isinstance(doc_data, dict) and doc_data.get("url"):
                doc_status = document_status.get(doc_type, {}).get("status", "pending")
                doc_notes = document_notes.get(doc_type, {}).get("notes")
                document_list.append(
                    {
                        "type": doc_type,
                        "name": doc_data.get(
                            "name", doc_type.replace("_", " ").title()
                        ),
                        "url": doc_data["url"],
                        "uploaded_at": doc_data.get("uploaded_at"),
                        "status": doc_status,
                        "notes": doc_notes,
                    }
                )

        return ResponseFactory.success(
            message="KYC documents retrieved successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "documents": document_list,
                "total_documents": len(document_list),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get KYC documents")


def approve_document(
    church_id: int,
    document_type: str,
    actor_id: int,
    db: Session,
    notes: Optional[str] = None,
) -> SuccessResponse:
    """Approve a specific KYC document"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Parse document status
        document_status = {}
        if church.document_status:
            if isinstance(church.document_status, dict):
                document_status = church.document_status
            elif isinstance(church.document_status, str):
                try:
                    document_status = json.loads(church.document_status)
                except json.JSONDecodeError:

                    document_status = {}
            else:
                document_status = {}

        # Update document status
        document_status[document_type] = {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": actor_id,
            "notes": notes,
        }

        # Update church record
        church.document_status = document_status
        db.commit()

        # Log the action
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="DOCUMENT_APPROVED",
            details_json={"document_type": document_type, "notes": notes},
        )
        db.add(audit_log)
        db.commit()

        # Send notification to church admins
        try:
            from app.services.notification_service import NotificationService

            NotificationService.notify_document_approved(
                church, document_type, notes or "", db
            )
        except Exception as e:
            pass

        return ResponseFactory.success(
            message=f"Document {document_type} approved successfully",
            data={
                "church_id": church_id,
                "document_type": document_type,
                "status": "approved",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to approve document")


def reject_document(
    church_id: int,
    document_type: str,
    actor_id: int,
    reason: str,
    db: Session,
    notes: Optional[str] = None,
) -> SuccessResponse:
    """Reject a specific KYC document"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Parse document status
        document_status = {}
        if church.document_status:
            if isinstance(church.document_status, dict):
                document_status = church.document_status
            elif isinstance(church.document_status, str):
                try:
                    document_status = json.loads(church.document_status)
                except json.JSONDecodeError:

                    document_status = {}
            else:
                document_status = {}

        # Update document status
        document_status[document_type] = {
            "status": "rejected",
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "rejected_by": actor_id,
            "reason": reason,
            "notes": notes,
        }

        # Update church record
        church.document_status = document_status
        db.commit()

        # Log the action
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="DOCUMENT_REJECTED",
            details_json={
                "document_type": document_type,
                "reason": reason,
                "notes": notes,
            },
        )
        db.add(audit_log)
        db.commit()

        # Send notification to church admins
        try:
            from app.services.notification_service import NotificationService

            NotificationService.notify_document_rejected(
                church, document_type, reason, notes or "", db
            )
        except Exception as e:
            pass

        return ResponseFactory.success(
            message=f"Document {document_type} rejected",
            data={
                "church_id": church_id,
                "document_type": document_type,
                "status": "rejected",
                "reason": reason,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reject document")


def request_documents(
    church_id: int,
    actor_id: int,
    required_documents: list,
    db: Session,
    notes: Optional[str] = None,
) -> SuccessResponse:
    """Request additional documents from church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Clear old document requests and start fresh
        document_requests = {}
        request_id = str(uuid.uuid4())
        document_requests[request_id] = {
            "required_documents": required_documents,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": actor_id,
            "notes": notes,
            "status": "pending",
        }

        # Clear old document notes and start fresh with new requests
        document_notes = {}

        # Add notes for each requested document
        for doc_type in required_documents:
            # Convert display names to document type keys
            doc_type_key = doc_type.lower().replace(" ", "_")
            if doc_type == "Articles of Incorporation":
                doc_type_key = "articles_of_incorporation"
            elif doc_type == "IRS Tax Exempt Letter":
                doc_type_key = "tax_exempt_letter"
            elif doc_type == "Bank Statement":
                doc_type_key = "bank_statement"
            elif doc_type == "Board Resolution":
                doc_type_key = "board_resolution"
            elif doc_type == "Other":
                doc_type_key = "other"

            document_notes[doc_type_key] = {
                "notes": f"Document requested by admin: {notes or 'Additional documentation needed'}",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "requested_by": actor_id,
                "status": "requested",
            }

        # Update church record
        church.document_requests = document_requests
        church.document_notes = document_notes
        db.commit()

        # Log the action
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            action="DOCUMENTS_REQUESTED",
            resource_type="church",
            resource_id=church_id,
            additional_data={"required_documents": required_documents, "notes": notes},
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Document request sent successfully",
            data={
                "church_id": church_id,
                "request_id": request_id,
                "required_documents": required_documents,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to request documents")


def add_document_notes(
    church_id: int, document_type: str, actor_id: int, notes: str, db: Session
) -> SuccessResponse:
    """Add notes to a specific document"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Parse document notes
        document_notes = {}
        if church.document_notes:
            if isinstance(church.document_notes, dict):
                document_notes = church.document_notes
            elif isinstance(church.document_notes, str):
                try:
                    document_notes = json.loads(church.document_notes)
                except json.JSONDecodeError:

                    document_notes = {}
            else:
                document_notes = {}

        # Add or update notes
        document_notes[document_type] = {
            "notes": notes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": actor_id,
        }

        # Update church record
        church.document_notes = document_notes
        db.commit()

        # Log the action
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="DOCUMENT_NOTES_ADDED",
            details_json={"document_type": document_type, "notes": notes},
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Document notes added successfully",
            data={
                "church_id": church_id,
                "document_type": document_type,
                "notes": notes,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add document notes")


def regenerate_kyc_link(church_id: int, actor_id: int, db: Session) -> SuccessResponse:
    """Regenerate onboarding link for a church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if not church.stripe_account_id:
            raise HTTPException(
                status_code=400, detail="No Stripe account found for this church"
            )

        # Generate new onboarding link
        onboarding_url = KYCService.generate_onboarding_link(church, db)

        # Log the action
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="LINK_REGENERATED",
            details_json={
                "stripe_account_id": church.stripe_account_id,
                "onboarding_url": onboarding_url,
            },
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Onboarding link regenerated successfully",
            data={
                "onboarding_url": onboarding_url,
                "church_id": church_id,
                "church_name": church.name,
                "church_email": church.email,
            },
        )

    except HTTPException:
        raise
    except StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to regenerate onboarding link"
        )


def pause_payouts(church_id: int, actor_id: int, db: Session) -> SuccessResponse:
    """Pause payouts for a church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if not church.stripe_account_id:
            raise HTTPException(
                status_code=400, detail="No Stripe account found for this church"
            )

        # Pause payouts
        result = KYCService.pause_payouts(church, db, actor_id)

        return ResponseFactory.success(
            message="Payouts paused successfully", data=result
        )

    except HTTPException:
        raise
    except StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to pause payouts")


def resume_payouts(church_id: int, actor_id: int, db: Session) -> SuccessResponse:
    """Resume payouts for a church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if not church.stripe_account_id:
            raise HTTPException(
                status_code=400, detail="No Stripe account found for this church"
            )

        # Resume payouts
        result = KYCService.resume_payouts(church, db, actor_id)

        return ResponseFactory.success(
            message="Payouts resumed successfully", data=result
        )

    except HTTPException:
        raise
    except StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to resume payouts")


def add_admin_notes(
    church_id: int, actor_id: int, notes: str, db: Session
) -> SuccessResponse:
    """Add internal notes for a church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Log the notes
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="NOTES_ADDED",
            details_json={
                "notes": notes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Notes added successfully",
            data={
                "church_id": church_id,
                "notes": notes,
                "added_by": actor_id,
                "timestamp": audit_log.created_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add notes")


def get_audit_logs(
    db: Session, church_id: Optional[int] = None, page: int = 1, limit: int = 50
) -> SuccessResponse:
    """Get audit logs for churches"""
    try:
        query = db.query(AuditLog)

        # Filter by church if provided
        if church_id:
            query = query.filter(AuditLog.church_id == church_id)

        # Pagination
        total = query.count()
        logs = (
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        # Format response data
        log_data = []
        for log in logs:
            log_data.append(
                {
                    "id": log.id,
                    "actor_type": log.actor_type,
                    "actor_id": log.actor_id,
                    "church_id": log.church_id,
                    "action": log.action,
                    "details": log.details_json,
                    "created_at": log.created_at,
                }
            )

        return ResponseFactory.success(
            message="Audit logs retrieved successfully",
            data={
                "logs": log_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get audit logs")


def approve_kyc(
    church_id: int, actor_id: int, approval_notes: str, db: Session
) -> SuccessResponse:
    """Approve KYC for a church"""
    try:
        # Get church
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if church.kyc_status not in ["pending", "under_review", "needs_info"]:
            raise HTTPException(
                status_code=400,
                detail=f"KYC application is in {church.kyc_status} status, cannot approve",
            )

        # Update KYC status
        previous_status = church.kyc_status
        church.kyc_status = "approved"
        church.kyc_approved_at = datetime.now(timezone.utc)
        church.kyc_approved_by = actor_id
        church.kyc_state = "ACTIVE"
        church.status = "active"
        church.verified_at = datetime.now(timezone.utc)
        church.updated_at = datetime.now(timezone.utc)

        # Log the approval
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="KYC_APPROVED",
            details_json={
                "previous_status": previous_status,
                "new_status": "approved",
                "approval_notes": approval_notes,
                "approved_at": church.kyc_approved_at.isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        # Send notification to church admins
        try:
            NotificationService.notify_kyc_approved(church, approval_notes, db)
        except Exception as e:
            pass

        return ResponseFactory.success(
            message="KYC approved successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "previous_status": previous_status,
                "new_status": "approved",
                "approved_by": actor_id,
                "approved_at": church.kyc_approved_at,
                "approval_notes": approval_notes,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to approve KYC")


def reject_kyc(
    church_id: int, actor_id: int, rejection_reason: str, db: Session
) -> SuccessResponse:
    """Reject KYC for a church"""
    try:
        # Get church
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if church.kyc_status not in ["pending", "under_review", "needs_info"]:
            raise HTTPException(
                status_code=400,
                detail=f"KYC application is in {church.kyc_status} status, cannot reject",
            )

        # Update KYC status
        previous_status = church.kyc_status
        church.kyc_status = "rejected"
        church.kyc_rejected_at = datetime.now(timezone.utc)
        church.kyc_rejected_by = actor_id
        church.kyc_rejection_reason = rejection_reason
        church.kyc_state = "REJECTED"
        church.status = "kyc_rejected"
        church.updated_at = datetime.now(timezone.utc)

        # Log the rejection
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="KYC_REJECTED",
            details_json={
                "previous_status": previous_status,
                "new_status": "rejected",
                "rejection_reason": rejection_reason,
                "rejected_at": church.kyc_rejected_at.isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        # Send notification to church admins
        try:
            NotificationService.notify_kyc_rejected(church, rejection_reason, db)
        except Exception as e:
            pass

        return ResponseFactory.success(
            message="KYC rejected successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "previous_status": previous_status,
                "new_status": "rejected",
                "rejected_by": actor_id,
                "rejected_at": church.kyc_rejected_at,
                "rejection_reason": rejection_reason,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reject KYC")


def request_kyc_info(
    church_id: int, actor_id: int, required_info: str, db: Session
) -> SuccessResponse:
    """Request additional information for KYC"""
    try:
        # Get church
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if church.kyc_status not in ["pending", "under_review"]:
            raise HTTPException(
                status_code=400,
                detail=f"KYC application is in {church.kyc_status} status, cannot request additional info",
            )

        # Update KYC status
        previous_status = church.kyc_status
        church.kyc_status = "needs_info"
        church.kyc_state = "KYC_NEEDS_INFO"
        church.updated_at = datetime.now(timezone.utc)

        # Log the request
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="KYC_INFO_REQUESTED",
            details_json={
                "previous_status": previous_status,
                "new_status": "needs_info",
                "required_info": required_info,
                "requested_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        # Send notification to church admins
        try:
            NotificationService.notify_kyc_info_requested(church, required_info, db)
        except Exception as e:
            pass

        return ResponseFactory.success(
            message="Additional information requested successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "previous_status": previous_status,
                "new_status": "needs_info",
                "requested_by": actor_id,
                "required_info": required_info,
                "requested_at": audit_log.created_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to request additional information"
        )


def add_admin_notes(
    church_id: int, actor_id: int, notes: str, db: Session
) -> SuccessResponse:
    """Add internal admin notes for a church"""
    try:
        # Get church
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Update admin notes
        church.admin_notes = notes
        church.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Log the action
        audit_log = AuditLog(
            actor_type="internal_admin",
            actor_id=actor_id,
            church_id=church_id,
            action="NOTES_ADDED",
            details_json={
                "notes": notes,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "added_by": actor_id,
            },
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Admin notes added successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "notes": notes,
                "added_at": audit_log.created_at,
                "added_by": actor_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add admin notes")


def get_kyc_confirmation_queue(
    db: Session, page: int = 1, limit: int = 20
) -> SuccessResponse:
    """Get churches that need KYC confirmation (pending or under_review)"""
    try:
        from app.model.m_church_admin import ChurchAdmin

        # Query Church model for pending applications
        query = db.query(Church).filter(
            Church.kyc_status.in_(["pending", "under_review", "needs_info"])
        )

        # Pagination
        total = query.count()
        churches = query.offset((page - 1) * limit).limit(limit).all()

        # Format response data
        church_data = []
        for church in churches:
            admin = db.query(ChurchAdmin).filter_by(church_id=church.id).first()

            # Get recent audit logs for context
            recent_logs = (
                db.query(AuditLog)
                .filter(AuditLog.church_id == church.id)
                .order_by(AuditLog.created_at.desc())
                .limit(5)
                .all()
            )

            log_data = []
            for log in recent_logs:
                log_data.append(
                    {
                        "action": log.action,
                        "details": log.details_json,
                        "created_at": log.created_at,
                    }
                )

            church_data.append(
                {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "phone": church.phone,
                    "kyc_state": church.kyc_status,  # Use Church kyc_status
                    "charges_enabled": church.charges_enabled,
                    "payouts_enabled": church.payouts_enabled,
                    "stripe_account_id": church.stripe_account_id,
                    "created_at": church.created_at,
                    "updated_at": church.updated_at,
                    "submitted_at": church.kyc_submitted_at,
                    "requirements_count": 0,  # Will be calculated based on missing documents
                    "recent_activity": log_data,
                    "admin": {
                        "id": admin.id if admin else None,
                        "email": admin.user.email if admin and admin.user else None,
                        "name": (
                            f"{admin.user.first_name} {admin.user.last_name}"
                            if admin and admin.user
                            else None
                        ),
                    },
                }
            )

        return ResponseFactory.success(
            message="KYC confirmation queue retrieved successfully",
            data={
                "churches": church_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to get KYC confirmation queue"
        )
