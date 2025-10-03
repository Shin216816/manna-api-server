"""
Church KYC Compliance Controller

Handles comprehensive KYC compliance functionality:
- Complete KYC submission with all required documents
- Beneficial ownership disclosure
- Compliance attestations
- Document verification and validation
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.model.m_church import Church
from app.model.m_beneficial_owner import BeneficialOwner
from app.model.m_audit_log import AuditLog
from app.schema.church_schema import ChurchKYCRequest, ControlPersonRequest
from app.core.responses import ResponseFactory
from app.core.exceptions import ValidationError, NotFoundError
from app.utils.error_handler import handle_controller_errors
from app.utils.file_upload import upload_file
from fastapi import HTTPException, UploadFile


@handle_controller_errors
def submit_comprehensive_kyc(church_id: int, kyc_data: ChurchKYCRequest, db: Session) -> ResponseFactory:
    """Submit comprehensive KYC with all compliance requirements"""
    try:
        # Validate church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise NotFoundError("Church not found")

        # Validate all required attestations are true
        required_attestations = [
            kyc_data.tax_exempt,
            kyc_data.anti_terrorism,
            kyc_data.legitimate_entity,
            kyc_data.consent_checks,
            kyc_data.beneficial_ownership_disclosure,
            kyc_data.information_accuracy,
            kyc_data.penalty_of_perjury
        ]
        
        if not all(required_attestations):
            raise ValidationError("All compliance attestations must be accepted")

        # Validate control persons are provided
        if not kyc_data.control_persons or len(kyc_data.control_persons) == 0:
            raise ValidationError("At least one control person must be provided")

        # Update church with KYC information
        church.legal_name = kyc_data.legal_name
        church.ein = kyc_data.ein
        church.website = kyc_data.website
        church.phone = kyc_data.phone
        church.email = kyc_data.email
        church.address = kyc_data.address
        church.address_line_2 = kyc_data.address_line_2
        church.city = kyc_data.city
        church.state = kyc_data.state
        church.zip_code = kyc_data.zip_code
        church.country = kyc_data.country
        church.primary_purpose = kyc_data.primary_purpose
        church.formation_date = kyc_data.formation_date
        church.formation_state = kyc_data.formation_state
        
        # Set KYC status
        church.kyc_status = "pending"
        church.kyc_submitted_at = datetime.now(timezone.utc)
        
        # Store compliance attestations
        church.tax_exempt = kyc_data.tax_exempt
        church.anti_terrorism = kyc_data.anti_terrorism
        church.legitimate_entity = kyc_data.legitimate_entity
        church.consent_checks = kyc_data.consent_checks
        church.beneficial_ownership_disclosure = kyc_data.beneficial_ownership_disclosure
        church.information_accuracy = kyc_data.information_accuracy
        church.penalty_of_perjury = kyc_data.penalty_of_perjury

        # Store document paths
        church.articles_of_incorporation = kyc_data.articles_of_incorporation
        church.tax_exempt_letter = kyc_data.tax_exempt_letter
        church.bank_statement = kyc_data.bank_statement
        church.board_resolution = kyc_data.board_resolution

        # Clear existing beneficial owners
        db.query(BeneficialOwner).filter(BeneficialOwner.church_id == church_id).delete()

        # Add new beneficial owners/control persons
        for i, control_person in enumerate(kyc_data.control_persons):
            beneficial_owner = BeneficialOwner(
                church_id=church_id,
                first_name=control_person.first_name,
                last_name=control_person.last_name,
                title=control_person.title,
                is_primary=control_person.is_primary,
                date_of_birth=control_person.date_of_birth,
                ssn_full=control_person.ssn_full,
                phone=control_person.phone,
                email=control_person.email,
                address_line_1=control_person.address.get("address_line_1", ""),
                address_line_2=control_person.address.get("address_line_2", ""),
                city=control_person.address.get("city", ""),
                state=control_person.address.get("state", ""),
                zip_code=control_person.address.get("zip_code", ""),
                country=control_person.address.get("country", ""),
                gov_id_type=control_person.gov_id_type,
                gov_id_number=control_person.gov_id_number,
                gov_id_front=control_person.gov_id_front,
                gov_id_back=control_person.gov_id_back,
                country_of_citizenship=control_person.country_of_citizenship,
                country_of_residence=control_person.country_of_residence,
                created_at=datetime.now(timezone.utc)
            )
            db.add(beneficial_owner)

        # Log audit event
        log_audit_event(
            db=db,
            actor_type="church_admin",
            actor_id=church_id,
            action="KYC_SUBMITTED",
            metadata={
                "resource_type": "church",
                "resource_id": church_id,
                "kyc_status": "pending_review",
                "control_persons_count": len(kyc_data.control_persons),
                "compliance_attestations": {
                    "tax_exempt": kyc_data.tax_exempt,
                    "anti_terrorism": kyc_data.anti_terrorism,
                    "legitimate_entity": kyc_data.legitimate_entity,
                    "consent_checks": kyc_data.consent_checks,
                    "beneficial_ownership_disclosure": kyc_data.beneficial_ownership_disclosure,
                    "information_accuracy": kyc_data.information_accuracy,
                    "penalty_of_perjury": kyc_data.penalty_of_perjury
                }
            }
        )

        db.commit()

        return ResponseFactory.success(
            message="KYC submitted successfully for review",
            data={
                "church_id": church_id,
                "kyc_status": "pending_review",
                "submitted_at": church.kyc_submitted_at.isoformat(),
                "control_persons_count": len(kyc_data.control_persons),
                "next_steps": "Your KYC submission is under review. You will be notified once approved."
            }
        )

    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error submitting KYC: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit KYC")


@handle_controller_errors
def upload_kyc_document(
    church_id: int, 
    document_type: str, 
    file: UploadFile, 
    db: Session
) -> ResponseFactory:
    """Upload KYC compliance documents"""
    try:
        # Validate church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise NotFoundError("Church not found")

        # Validate document type
        allowed_types = [
            "articles_of_incorporation",
            "tax_exempt_letter", 
            "bank_statement",
            "board_resolution",
            "gov_id_front",
            "gov_id_back"
        ]
        
        if document_type not in allowed_types:
            raise ValidationError(f"Invalid document type. Allowed types: {', '.join(allowed_types)}")

        # Upload file
        file_path = upload_file(
            file=file,
            folder=f"church_docs/{church_id}",
            allowed_extensions=[".pdf", ".jpg", ".jpeg", ".png"]
        )

        # Update church record with document path
        if document_type == "articles_of_incorporation":
            church.articles_of_incorporation = file_path
        elif document_type == "tax_exempt_letter":
            church.tax_exempt_letter = file_path
        elif document_type == "bank_statement":
            church.bank_statement = file_path
        elif document_type == "board_resolution":
            church.board_resolution = file_path

        # Log audit event
        log_audit_event(
            db=db,
            actor_type="church_admin",
            actor_id=church_id,
            action="KYC_DOCUMENT_UPLOADED",
            metadata={
                "resource_type": "church",
                "resource_id": church_id,
                "document_type": document_type,
                "file_path": file_path
            }
        )

        db.commit()

        return ResponseFactory.success(
            message="Document uploaded successfully",
            data={
                "document_type": document_type,
                "file_path": file_path,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
        )

    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to upload document")


@handle_controller_errors
def get_kyc_compliance_status(church_id: int, db: Session) -> ResponseFactory:
    """Get comprehensive KYC compliance status"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise NotFoundError("Church not found")

        # Get beneficial owners
        beneficial_owners = db.query(BeneficialOwner).filter(
            BeneficialOwner.church_id == church_id
        ).all()

        # Check compliance completeness
        compliance_checklist = {
            "legal_information": bool(church.legal_name and church.ein and church.address),
            "control_persons": len(beneficial_owners) > 0,
            "required_documents": {
                "articles_of_incorporation": bool(church.articles_of_incorporation),
                "tax_exempt_letter": bool(church.tax_exempt_letter),
                "bank_statement": bool(church.bank_statement),
                "board_resolution": bool(church.board_resolution)
            },
            "compliance_attestations": {
                "tax_exempt": church.tax_exempt,
                "anti_terrorism": church.anti_terrorism,
                "legitimate_entity": church.legitimate_entity,
                "consent_checks": church.consent_checks,
                "beneficial_ownership_disclosure": church.beneficial_ownership_disclosure,
                "information_accuracy": church.information_accuracy,
                "penalty_of_perjury": church.penalty_of_perjury
            }
        }

        # Calculate completion percentage
        total_checks = 2 + len(compliance_checklist["required_documents"]) + len(compliance_checklist["compliance_attestations"])
        completed_checks = sum([
            compliance_checklist["legal_information"],
            compliance_checklist["control_persons"]
        ]) + sum(compliance_checklist["required_documents"].values()) + sum(compliance_checklist["compliance_attestations"].values())
        
        completion_percentage = (completed_checks / total_checks) * 100

        # Prepare beneficial owners data
        control_persons_data = []
        for owner in beneficial_owners:
            control_persons_data.append({
                "id": owner.id,
                "first_name": owner.first_name,
                "last_name": owner.last_name,
                "title": owner.title,
                "is_primary": owner.is_primary,
                "date_of_birth": owner.date_of_birth,
                "phone": owner.phone,
                "email": owner.email,
                "address": {
                    "address_line_1": owner.address_line_1,
                    "address_line_2": owner.address_line_2,
                    "city": owner.city,
                    "state": owner.state,
                    "zip_code": owner.zip_code,
                    "country": owner.country
                },
                "gov_id_type": owner.gov_id_type,
                "gov_id_number": owner.gov_id_number,
                "gov_id_front": owner.gov_id_front,
                "gov_id_back": owner.gov_id_back,
                "country_of_citizenship": owner.country_of_citizenship,
                "country_of_residence": owner.country_of_residence
            })

        return ResponseFactory.success(
            message="KYC compliance status retrieved successfully",
            data={
                "church_id": church_id,
                "kyc_status": church.kyc_status,
                "completion_percentage": round(completion_percentage, 1),
                "compliance_checklist": compliance_checklist,
                "control_persons": control_persons_data,
                "legal_information": {
                    "legal_name": church.legal_name,
                    "ein": church.ein,
                    "website": church.website,
                    "phone": church.phone,
                    "email": church.email,
                    "address": church.address,
                    "address_line_2": church.address_line_2,
                    "city": church.city,
                    "state": church.state,
                    "zip_code": church.zip_code,
                    "country": church.country,
                    "primary_purpose": church.primary_purpose,
                    "formation_date": church.formation_date,
                    "formation_state": church.formation_state
                },
                "required_documents": {
                    "articles_of_incorporation": church.articles_of_incorporation,
                    "tax_exempt_letter": church.tax_exempt_letter,
                    "bank_statement": church.bank_statement,
                    "board_resolution": church.board_resolution
                },
                "submitted_at": church.kyc_submitted_at.isoformat() if church.kyc_submitted_at else None,
                "last_updated": church.updated_at.isoformat() if church.updated_at else None
            }
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting KYC compliance status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get KYC compliance status")


def log_audit_event(db: Session, actor_type: str, actor_id: int, action: str, metadata: Dict[str, Any]):
    """Log audit event for compliance tracking"""
    try:
        audit_log = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        db.add(audit_log)
    except Exception as e:
        logging.error(f"Failed to log audit event: {str(e)}")
        # Don't raise exception for audit logging failures
