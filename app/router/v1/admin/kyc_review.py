"""
KYC Review Router

Handles KYC review and approval workflow for Manna admin team.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.utils.database import get_db
from app.middleware.admin_auth import admin_auth
from app.model.m_church import Church
from app.model.m_beneficial_owner import BeneficialOwner
from app.core.responses import ResponseFactory
from app.core.exceptions import ValidationError
from app.utils.error_handler import handle_controller_errors

router = APIRouter()

@router.get("/pending-kyc")
async def get_pending_kyc_submissions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query("", description="Filter by KYC status"),
    search: str = Query("", description="Search by church name, email, EIN, or admin name"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get all KYC submissions for review with comprehensive filtering"""
    try:
        offset = (page - 1) * limit
        
        # Build query with status filtering
        query = db.query(Church)
        
        # Always exclude not_submitted status for KYC review
        query = query.filter(Church.kyc_status != 'not_submitted')
        
        # Filter by status if provided
        if status and status != "all":
            if status == "pending":
                query = query.filter(Church.kyc_status.in_(['pending', 'pending_review', 'under_review', 'needs_info']))
            elif status == "approved":
                query = query.filter(Church.kyc_status == 'approved')
            elif status == "rejected":
                query = query.filter(Church.kyc_status == 'rejected')
            elif status == "needs_info":
                query = query.filter(Church.kyc_status == 'needs_info')
            elif status == "under_review":
                query = query.filter(Church.kyc_status == 'under_review')
        
        # Search functionality
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Church.name.ilike(search_term),
                    Church.email.ilike(search_term),
                    Church.ein.ilike(search_term),
                    Church.legal_name.ilike(search_term)
                )
            )
        
        # Sorting functionality
        valid_sort_fields = {
            'created_at': Church.created_at,
            'name': Church.name,
            'email': Church.email,
            'kyc_status': Church.kyc_status,
            'updated_at': Church.updated_at
        }
        
        if sort_by in valid_sort_fields:
            sort_field = valid_sort_fields[sort_by]
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())
        else:
            # Default sorting by created_at desc
            query = query.order_by(Church.created_at.desc())
        
        # Get total count
        total_count = query.count()
        
        # Get churches with pagination
        churches = query.offset(offset).limit(limit).all()
        
        # Format response data
        kyc_submissions = []
        for church in churches:
            # Get beneficial owners
            beneficial_owners = db.query(BeneficialOwner).filter(
                BeneficialOwner.church_id == church.id
            ).all()
            
            # Get church admin
            from app.model.m_church_admin import ChurchAdmin
            church_admin = db.query(ChurchAdmin).filter(
                ChurchAdmin.church_id == church.id
            ).first()
            
            # Calculate completion percentage
            completion_percentage = _calculate_kyc_completion_percentage(church, beneficial_owners)
            
            # Get documents status
            documents = {
                'articles_of_incorporation': {
                    'url': church.articles_of_incorporation,
                    'uploaded': bool(church.articles_of_incorporation),
                    'status': 'uploaded' if church.articles_of_incorporation else 'not_uploaded'
                },
                'tax_exempt_letter': {
                    'url': church.tax_exempt_letter,
                    'uploaded': bool(church.tax_exempt_letter),
                    'status': 'uploaded' if church.tax_exempt_letter else 'not_uploaded'
                },
                'bank_statement': {
                    'url': church.bank_statement,
                    'uploaded': bool(church.bank_statement),
                    'status': 'uploaded' if church.bank_statement else 'not_uploaded'
                },
                'board_resolution': {
                    'url': church.board_resolution,
                    'uploaded': bool(church.board_resolution),
                    'status': 'uploaded' if church.board_resolution else 'not_uploaded'
                }
            }
            
            # Get attestations
            attestations = {
                'tax_exempt': church.tax_exempt,
                'anti_terrorism': church.anti_terrorism,
                'legitimate_entity': church.legitimate_entity,
                'consent_checks': church.consent_checks,
                'beneficial_ownership_disclosure': church.beneficial_ownership_disclosure,
                'information_accuracy': church.information_accuracy,
                'penalty_of_perjury': church.penalty_of_perjury
            }
            
            kyc_submissions.append({
                'id': church.id,
                'name': church.name,
                'legal_name': church.legal_name,
                'ein': church.ein,
                'website': church.website,
                'phone': church.phone,
                'email': church.email,
                'address_line_1': church.address_line_1 or church.address,
                'address_line_2': church.address_line_2,
                'city': church.city,
                'state': church.state,
                'zip_code': church.zip_code,
                'country': church.country,
                'primary_purpose': church.primary_purpose,
                'kyc_status': church.kyc_status,
                'kyc_state': church.kyc_state,
                'stripe_account_id': church.stripe_account_id,
                'charges_enabled': church.charges_enabled,
                'payouts_enabled': church.payouts_enabled,
                'disabled_reason': church.disabled_reason,
                'created_at': church.created_at.isoformat() if church.created_at else None,
                'updated_at': church.updated_at.isoformat() if church.updated_at else None,
                'kyc_submitted_at': church.kyc_submitted_at.isoformat() if church.kyc_submitted_at else None,
                'kyc_approved_at': church.kyc_approved_at.isoformat() if church.kyc_approved_at else None,
                'kyc_rejected_at': church.kyc_rejected_at.isoformat() if church.kyc_rejected_at else None,
                'kyc_rejection_reason': church.kyc_rejection_reason,
                'validation': {
                    'completeness_percentage': completion_percentage,
                    'documents_uploaded': _count_uploaded_documents(church),
                    'total_documents': 4,
                },
                'admin': {
                    'id': church_admin.id if church_admin else None,
                    'name': f"{church_admin.user.first_name} {church_admin.user.last_name}" if church_admin and church_admin.user else None,
                    'email': church_admin.user.email if church_admin and church_admin.user else None,
                } if church_admin else None,
                'beneficial_owners': [
                    {
                        'id': bo.id,
                        'first_name': bo.first_name,
                        'last_name': bo.last_name,
                        'full_name': f"{bo.first_name} {bo.last_name}",
                        'title': bo.title,
                        'is_primary': bo.is_primary,
                        'date_of_birth': bo.date_of_birth.isoformat() if bo.date_of_birth else None,
                        'ssn': bo.ssn_full,  # For frontend compatibility
                        'ssn_last_four': bo.ssn_full[-4:] if bo.ssn_full else None,
                        'email': bo.email,
                        'phone': bo.phone,
                        'address_line_1': bo.address_line_1,
                        'address_line_2': bo.address_line_2,
                        'city': bo.city,
                        'state': bo.state,
                        'zip_code': bo.zip_code,
                        'country': bo.country,
                        'id_type': bo.gov_id_type,
                        'id_number': bo.gov_id_number,
                        'id_front_url': bo.gov_id_front,
                        'id_back_url': bo.gov_id_back
                    }
                    for bo in beneficial_owners
                ],
                'documents': documents,
                'attestations': attestations,
                'total_owners': len(beneficial_owners)
            })
        
        return ResponseFactory.success(
            message="KYC submissions retrieved successfully",
            data={
                'churches': kyc_submissions,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'total_pages': (total_count + limit - 1) // limit
                }
            }
        )
    except Exception as e:
        return ResponseFactory.error(f"Error retrieving KYC submissions: {str(e)}", "500")


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
            owner.ssn_full,
            owner.address_line_1,
        ]
        total_fields += len(owner_fields)
        completed_fields += sum(1 for field in owner_fields if field)
    
    return int((completed_fields / total_fields * 100)) if total_fields > 0 else 0


def _count_uploaded_documents(church: Church) -> int:
    """Count uploaded documents"""
    doc_fields = [
        church.articles_of_incorporation,
        church.tax_exempt_letter,
        church.bank_statement,
        church.board_resolution,
    ]
    return sum(1 for field in doc_fields if field)

def _calculate_document_completion_percentage(church: Church) -> int:
    """Calculate document completion percentage"""
    doc_fields = [
        church.articles_of_incorporation,
        church.tax_exempt_letter,
        church.bank_statement,
        church.board_resolution,
    ]
    uploaded_count = sum(1 for field in doc_fields if field)
    return int((uploaded_count / len(doc_fields)) * 100) if doc_fields else 0

def _count_completed_fields(church: Church, beneficial_owners: list) -> int:
    """Count completed fields for completion status"""
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
            owner.ssn_full,
            owner.address_line_1,
        ]
        total_fields += len(owner_fields)
        completed_fields += sum(1 for field in owner_fields if field)
    
    return completed_fields

def _count_total_fields() -> int:
    """Count total fields for completion status"""
    # This is a simplified count - in practice you'd want to match the actual field count
    return 25  # Approximate total fields across church info, documents, and beneficial owners

@router.get("/kyc-submission/{church_id}")
async def get_kyc_submission_details(
    church_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get detailed KYC submission for a specific church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        # Get beneficial owners
        beneficial_owners = db.query(BeneficialOwner).filter(
            BeneficialOwner.church_id == church.id
        ).all()
        
        # Get church admin
        from app.model.m_church_admin import ChurchAdmin
        church_admin = db.query(ChurchAdmin).filter(
            ChurchAdmin.church_id == church.id
        ).first()
        
        # Get audit logs
        from app.model.m_audit_log import AuditLog
        audit_logs = db.query(AuditLog).filter(
            AuditLog.resource_type == 'church',
            AuditLog.resource_id == church_id
        ).order_by(AuditLog.created_at.desc()).limit(10).all()
        
        # Build comprehensive response matching frontend expectations
        return ResponseFactory.success(
            message="KYC submission details retrieved successfully",
            data={
                'church': {
                    'id': church.id,
                    'name': church.name,
                    'legal_name': church.legal_name,
                    'email': church.email,
                    'phone': church.phone,
                    'address': church.address_line_1 or church.address,
                    'city': church.city,
                    'state': church.state,
                    'zip_code': church.zip_code,
                    'country': church.country,
                    'website': church.website,
                    'ein': church.ein,
                    'primary_purpose': church.primary_purpose,
                    'kyc_status': church.kyc_status,
                    'kyc_state': church.kyc_state,
                    'charges_enabled': church.charges_enabled,
                    'payouts_enabled': church.payouts_enabled,
                    'disabled_reason': church.disabled_reason,
                    'created_at': church.created_at.isoformat() if church.created_at else None,
                    'updated_at': church.updated_at.isoformat() if church.updated_at else None,
                },
                'kyc_data': {
                    'legal_information': {
                        'legal_name': church.legal_name or church.name,
                        'ein': church.ein,
                        'website': church.website,
                        'phone': church.phone,
                        'email': church.email,
                        'address': church.address_line_1 or church.address,
                        'address_line_2': church.address_line_2,
                        'city': church.city,
                        'state': church.state,
                        'zip_code': church.zip_code,
                        'country': church.country or "US",
                        'primary_purpose': church.primary_purpose,
                        'formation_date': church.formation_date.isoformat() if church.formation_date else None,
                        'formation_state': church.formation_state,
                    },
                    'control_persons': [
                        {
                            'id': bo.id,
                            'first_name': bo.first_name,
                            'last_name': bo.last_name,
                            'title': bo.title,
                            'is_primary': bo.is_primary,
                            'date_of_birth': bo.date_of_birth.isoformat() if bo.date_of_birth else None,
                            'ssn': bo.ssn_full,
                            'ssn_last_four': bo.ssn_full[-4:] if bo.ssn_full else None,
                            'email': bo.email,
                            'phone': bo.phone,
                            'address_line_1': bo.address_line_1,
                            'address_line_2': bo.address_line_2,
                            'city': bo.city,
                            'state': bo.state,
                            'zip_code': bo.zip_code,
                            'country': bo.country,
                            'id_type': bo.gov_id_type,
                            'id_number': bo.gov_id_number,
                            'id_front_url': bo.gov_id_front,
                            'id_back_url': bo.gov_id_back
                        }
                        for bo in beneficial_owners
                    ],
                    'documents': {
                        'articles_of_incorporation': {
                            'url': church.articles_of_incorporation,
                            'uploaded': bool(church.articles_of_incorporation),
                            'status': 'uploaded' if church.articles_of_incorporation else 'not_uploaded',
                            'file_path': church.articles_of_incorporation,
                            'file_name': 'Articles of Incorporation' if church.articles_of_incorporation else None,
                        },
                        'tax_exempt_letter': {
                            'url': church.tax_exempt_letter,
                            'uploaded': bool(church.tax_exempt_letter),
                            'status': 'uploaded' if church.tax_exempt_letter else 'not_uploaded',
                            'file_path': church.tax_exempt_letter,
                            'file_name': 'IRS Tax Exempt Letter' if church.tax_exempt_letter else None,
                        },
                        'bank_statement': {
                            'url': church.bank_statement,
                            'uploaded': bool(church.bank_statement),
                            'status': 'uploaded' if church.bank_statement else 'not_uploaded',
                            'file_path': church.bank_statement,
                            'file_name': 'Bank Statement' if church.bank_statement else None,
                        },
                        'board_resolution': {
                            'url': church.board_resolution,
                            'uploaded': bool(church.board_resolution),
                            'status': 'uploaded' if church.board_resolution else 'not_uploaded',
                            'file_path': church.board_resolution,
                            'file_name': 'Board Resolution' if church.board_resolution else None,
                        }
                    },
                    'compliance_attestations': {
                        'tax_exempt': church.tax_exempt,
                        'anti_terrorism': church.anti_terrorism,
                        'legitimate_entity': church.legitimate_entity,
                        'consent_checks': church.consent_checks,
                        'beneficial_ownership_disclosure': church.beneficial_ownership_disclosure,
                        'information_accuracy': church.information_accuracy,
                        'penalty_of_perjury': church.penalty_of_perjury
                    },
                    'completion_status': {
                        'overall_percentage': _calculate_kyc_completion_percentage(church, beneficial_owners),
                        'document_percentage': _calculate_document_completion_percentage(church),
                        'completed_fields': _count_completed_fields(church, beneficial_owners),
                        'total_fields': _count_total_fields(),
                        'uploaded_documents': _count_uploaded_documents(church),
                        'total_documents': 4,
                    }
                },
                'stripe_information': {
                    'stripe_account_id': church.stripe_account_id,
                    'charges_enabled': church.charges_enabled,
                    'payouts_enabled': church.payouts_enabled,
                    'disabled_reason': church.disabled_reason,
                },
                'audit_logs': [
                    {
                        'id': log.id,
                        'actor_type': log.actor_type,
                        'actor_id': log.actor_id,
                        'action': log.action,
                        'details': log.details_json,
                        'created_at': log.created_at.isoformat() if log.created_at else None,
                    }
                    for log in audit_logs
                ],
                'submission_info': {
                    'submitted_at': church.kyc_submitted_at.isoformat() if church.kyc_submitted_at else None,
                    'approved_at': church.kyc_approved_at.isoformat() if church.kyc_approved_at else None,
                    'rejected_at': church.kyc_rejected_at.isoformat() if church.kyc_rejected_at else None,
                    'rejection_reason': church.kyc_rejection_reason,
                    'admin_notes': church.admin_notes,
                    'last_updated': church.updated_at.isoformat() if church.updated_at else None,
                }
            }
        )
    except Exception as e:
        return ResponseFactory.error(f"Error retrieving KYC submission details: {str(e)}", "500")

@router.post("/approve-kyc/{church_id}")
async def approve_kyc_submission(
    church_id: int,
    approval_notes: str = None,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Approve a KYC submission"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        if church.kyc_status != 'pending':
            return ResponseFactory.error(f"Church KYC status is {church.kyc_status}, not pending", "400")
        
        # Update church status
        church.kyc_status = 'approved'
        church.status = 'active'
        church.is_active = True
        
        # Add approval notes to KYC data
        if not church.kyc_data:
            church.kyc_data = {}
        church.kyc_data['approval_notes'] = approval_notes
        church.kyc_data['approved_by'] = current_user['user_id']
        church.kyc_data['approved_at'] = db.func.now()
        
        db.commit()
        
        # Log audit event
        from app.utils.audit import log_audit_event
        log_audit_event(
            db=db,
            user_id=current_user['user_id'],
            action='kyc_approved',
            resource_type='church',
            resource_id=church_id,
            details={'approval_notes': approval_notes}
        )
        
        return ResponseFactory.success(
            message="KYC submission approved successfully",
            data={
                'church_id': church_id,
                'status': 'approved',
                'approved_at': church.kyc_data.get('approved_at')
            }
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error approving KYC submission: {str(e)}", "500")

@router.post("/reject-kyc/{church_id}")
async def reject_kyc_submission(
    church_id: int,
    rejection_reason: str,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Reject a KYC submission"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        if church.kyc_status != 'pending':
            return ResponseFactory.error(f"Church KYC status is {church.kyc_status}, not pending", "400")
        
        # Update church status
        church.kyc_status = 'rejected'
        church.status = 'inactive'
        church.is_active = False
        
        # Add rejection reason to KYC data
        if not church.kyc_data:
            church.kyc_data = {}
        church.kyc_data['rejection_reason'] = rejection_reason
        church.kyc_data['rejected_by'] = current_user['user_id']
        church.kyc_data['rejected_at'] = db.func.now()
        
        db.commit()
        
        # Log audit event
        from app.utils.audit import log_audit_event
        log_audit_event(
            db=db,
            user_id=current_user['user_id'],
            action='kyc_rejected',
            resource_type='church',
            resource_id=church_id,
            details={'rejection_reason': rejection_reason}
        )
        
        return ResponseFactory.success(
            message="KYC submission rejected successfully",
            data={
                'church_id': church_id,
                'status': 'rejected',
                'rejection_reason': rejection_reason,
                'rejected_at': church.kyc_data.get('rejected_at')
            }
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error rejecting KYC submission: {str(e)}", "500")

@router.post("/request-kyc-info/{church_id}")
async def request_additional_kyc_info(
    church_id: int,
    info_request: str,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Request additional information for a KYC submission"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        if church.kyc_status != 'pending':
            return ResponseFactory.error(f"Church KYC status is {church.kyc_status}, not pending", "400")
        
        # Update KYC data with info request
        if not church.kyc_data:
            church.kyc_data = {}
        church.kyc_data['info_request'] = info_request
        church.kyc_data['info_requested_by'] = current_user['user_id']
        church.kyc_data['info_requested_at'] = db.func.now()
        
        db.commit()
        
        # Log audit event
        from app.utils.audit import log_audit_event
        log_audit_event(
            db=db,
            user_id=current_user['user_id'],
            action='kyc_info_requested',
            resource_type='church',
            resource_id=church_id,
            details={'info_request': info_request}
        )
        
        return ResponseFactory.success(
            message="Information request sent successfully",
            data={
                'church_id': church_id,
                'info_request': info_request,
                'requested_at': church.kyc_data.get('info_requested_at')
            }
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error requesting additional KYC info: {str(e)}", "500")

@router.get("/kyc-stats")
async def get_kyc_statistics(
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive KYC processing statistics"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timezone, timedelta
        
        # Get counts by status
        status_counts = db.query(
            Church.kyc_status,
            func.count(Church.id).label('count')
        ).group_by(Church.kyc_status).all()
        
        # Get recent submissions (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        recent_submissions = db.query(Church).filter(
            Church.created_at >= thirty_days_ago
        ).count()
        
        # Get average processing time
        approved_churches = db.query(Church).filter(
            Church.kyc_status == 'approved',
            Church.kyc_data.isnot(None)
        ).all()
        
        processing_times = []
        for church in approved_churches:
            if church.kyc_data and 'approved_at' in church.kyc_data:
                submitted_at = church.created_at
                approved_at = church.kyc_data['approved_at']
                if isinstance(approved_at, str):
                    from datetime import datetime
                    approved_at = datetime.fromisoformat(approved_at.replace('Z', '+00:00'))
                
                processing_time = (approved_at - submitted_at).days
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Get total applications count (exclude not_submitted)
        total_applications = db.query(Church).filter(
            Church.kyc_status != 'not_submitted'
        ).count()
        
        # Get pending count (includes pending, under_review, needs_info)
        pending_count = db.query(Church).filter(
            Church.kyc_status.in_(['pending', 'pending_review', 'under_review', 'needs_info'])
        ).count()
        
        # Get approved count
        approved_count = db.query(Church).filter(
            Church.kyc_status == 'approved'
        ).count()
        
        # Get rejected count
        rejected_count = db.query(Church).filter(
            Church.kyc_status == 'rejected'
        ).count()
        
        # Get needs info count
        needs_info_count = db.query(Church).filter(
            Church.kyc_status == 'needs_info'
        ).count()
        
        return ResponseFactory.success(
            message="KYC statistics retrieved successfully",
            data={
                'total_applications': total_applications,
                'pending_count': pending_count,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'needs_info_count': needs_info_count,
                'status_counts': {status: count for status, count in status_counts},
                'recent_submissions': recent_submissions,
                'average_processing_time_days': round(avg_processing_time, 1)
            }
        )
    except Exception as e:
        return ResponseFactory.error(f"Error retrieving KYC statistics: {str(e)}", "500")

@router.get("/{church_id}/documents")
async def get_kyc_documents(
    church_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get KYC documents for a specific church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        documents = {
            'articles_of_incorporation': {
                'url': church.articles_of_incorporation,
                'uploaded': bool(church.articles_of_incorporation),
                'status': 'uploaded' if church.articles_of_incorporation else 'not_uploaded',
                'file_path': church.articles_of_incorporation,
                'file_name': 'Articles of Incorporation' if church.articles_of_incorporation else None,
            },
            'tax_exempt_letter': {
                'url': church.tax_exempt_letter,
                'uploaded': bool(church.tax_exempt_letter),
                'status': 'uploaded' if church.tax_exempt_letter else 'not_uploaded',
                'file_path': church.tax_exempt_letter,
                'file_name': 'IRS Tax Exempt Letter' if church.tax_exempt_letter else None,
            },
            'bank_statement': {
                'url': church.bank_statement,
                'uploaded': bool(church.bank_statement),
                'status': 'uploaded' if church.bank_statement else 'not_uploaded',
                'file_path': church.bank_statement,
                'file_name': 'Bank Statement' if church.bank_statement else None,
            },
            'board_resolution': {
                'url': church.board_resolution,
                'uploaded': bool(church.board_resolution),
                'status': 'uploaded' if church.board_resolution else 'not_uploaded',
                'file_path': church.board_resolution,
                'file_name': 'Board Resolution' if church.board_resolution else None,
            }
        }
        
        return ResponseFactory.success(
            message="KYC documents retrieved successfully",
            data=documents
        )
    except Exception as e:
        return ResponseFactory.error(f"Error retrieving KYC documents: {str(e)}", "500")

@router.get("/{church_id}/stripe")
async def get_stripe_account_info(
    church_id: int,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Get Stripe account information for a specific church"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        stripe_info = {
            'stripe_account_id': church.stripe_account_id,
            'charges_enabled': church.charges_enabled,
            'payouts_enabled': church.payouts_enabled,
            'disabled_reason': church.disabled_reason,
            'kyc_state': church.kyc_state,
        }
        
        return ResponseFactory.success(
            message="Stripe account information retrieved successfully",
            data=stripe_info
        )
    except Exception as e:
        return ResponseFactory.error(f"Error retrieving Stripe account info: {str(e)}", "500")

@router.post("/{church_id}/documents/{document_type}/approve")
async def approve_document(
    church_id: int,
    document_type: str,
    notes: str = None,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Approve a KYC document"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        # Update document status in KYC data
        if not church.kyc_data:
            church.kyc_data = {}
        
        if 'documents' not in church.kyc_data:
            church.kyc_data['documents'] = {}
        
        church.kyc_data['documents'][document_type] = {
            'status': 'approved',
            'approved_by': current_user['user_id'],
            'approved_at': db.func.now(),
            'notes': notes
        }
        
        db.commit()
        
        return ResponseFactory.success(
            message=f"Document {document_type} approved successfully",
            data={'document_type': document_type, 'status': 'approved'}
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error approving document: {str(e)}", "500")

@router.post("/{church_id}/documents/{document_type}/reject")
async def reject_document(
    church_id: int,
    document_type: str,
    reason: str,
    notes: str = None,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Reject a KYC document"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        # Update document status in KYC data
        if not church.kyc_data:
            church.kyc_data = {}
        
        if 'documents' not in church.kyc_data:
            church.kyc_data['documents'] = {}
        
        church.kyc_data['documents'][document_type] = {
            'status': 'rejected',
            'rejected_by': current_user['user_id'],
            'rejected_at': db.func.now(),
            'reason': reason,
            'notes': notes
        }
        
        db.commit()
        
        return ResponseFactory.success(
            message=f"Document {document_type} rejected successfully",
            data={'document_type': document_type, 'status': 'rejected'}
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error rejecting document: {str(e)}", "500")

@router.post("/{church_id}/documents/{document_type}/notes")
async def add_document_notes(
    church_id: int,
    document_type: str,
    notes: str,
    current_user: dict = Depends(admin_auth),
    db: Session = Depends(get_db)
):
    """Add notes to a KYC document"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")
        
        # Update document notes in KYC data
        if not church.kyc_data:
            church.kyc_data = {}
        
        if 'documents' not in church.kyc_data:
            church.kyc_data['documents'] = {}
        
        if document_type not in church.kyc_data['documents']:
            church.kyc_data['documents'][document_type] = {}
        
        church.kyc_data['documents'][document_type]['notes'] = notes
        church.kyc_data['documents'][document_type]['notes_updated_by'] = current_user['user_id']
        church.kyc_data['documents'][document_type]['notes_updated_at'] = db.func.now()
        
        db.commit()
        
        return ResponseFactory.success(
            message=f"Notes added to document {document_type} successfully",
            data={'document_type': document_type, 'notes': notes}
        )
    except Exception as e:
        db.rollback()
        return ResponseFactory.error(f"Error adding document notes: {str(e)}", "500")
