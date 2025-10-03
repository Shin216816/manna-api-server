from fastapi import HTTPException, UploadFile
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.model.m_church import Church
from app.utils.file_upload import upload_file
from app.core.messages import get_auth_message
from app.core.responses import ResponseFactory, SuccessResponse


def get_church_profile(church_id: int, db: Session) -> SuccessResponse:
    """Get church profile"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        return ResponseFactory.success(
            message="Church profile retrieved successfully",
            data={
                "id": church.id,
                "name": church.name,
                "legal_name": church.legal_name,
                "ein": church.ein,
                "website": church.website,
                "phone": church.phone,
                "email": church.email,
                "address": church.address,
                "address_line_1": church.address_line_1,
                "address_line_2": church.address_line_2,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
                "country": church.country,
                "tax_id": church.ein,  # EIN is the tax ID
                "pastor_name": church.pastor_name,
                "primary_purpose": church.primary_purpose,
                "kyc_status": church.kyc_status,
                "status": church.status,
                "is_active": church.is_active,
                "referral_code": church.referral_code,
                "stripe_account_id": church.stripe_account_id,
                "charges_enabled": church.charges_enabled,
                "payouts_enabled": church.payouts_enabled,
                "total_received": (
                    float(church.total_received) if church.total_received else 0.0
                ),
                "created_at": church.created_at,
                "updated_at": church.updated_at,
                "kyc_submitted_at": church.kyc_submitted_at,
                "verified_at": church.verified_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get church profile")


def update_church_profile(
    church_id: int, profile_data: dict, db: Session
) -> SuccessResponse:
    """Update church profile"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        allowed_fields = [
            "name",
            "ein",
            "website",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "zip_code",
            "pastor_name",
        ]

        for field in allowed_fields:
            if field in profile_data and profile_data[field] is not None:
                setattr(church, field, profile_data[field])

        # Handle tax_id field - map it to ein
        if "tax_id" in profile_data and profile_data["tax_id"] is not None:
            church.ein = profile_data["tax_id"]

        church.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(church)

        return ResponseFactory.success(
            message="Church profile updated successfully",
            data={
                "id": church.id,
                "name": church.name,
                "ein": church.ein,
                "website": church.website,
                "phone": church.phone,
                "email": church.email,
                "address": church.address,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
                "tax_id": church.ein,  # EIN is the tax ID
                "pastor_name": church.pastor_name,
                "updated_at": church.updated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to update church profile")


def upload_church_logo(
    church_id: int, file: UploadFile, db: Session
) -> SuccessResponse:
    """Upload church logo"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG, PNG, and GIF are allowed",
            )

        if file.size and file.size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(
                status_code=400, detail="File size too large. Maximum 5MB allowed"
            )

        # Upload to local storage
        upload_result = upload_file(file, "church_logo")

        if upload_result["success"]:
            # Store logo URL in documents field as JSON
            import json

            documents = json.loads(church.documents) if church.documents else {}
            documents["logo"] = upload_result["url"]
            church.documents = json.dumps(documents)
            church.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(church)

            return ResponseFactory.success(
                message="Church logo uploaded successfully",
                data={"logo": upload_result["url"]},
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to upload logo")

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to upload church logo")


def update_church_contact(
    church_id: int, contact_data: dict, db: Session
) -> SuccessResponse:
    """Update church contact information"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        contact_fields = ["phone", "email", "address", "city", "state", "zip_code"]

        for field in contact_fields:
            if field in contact_data and contact_data[field] is not None:
                setattr(church, field, contact_data[field])

        church.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(church)

        return ResponseFactory.success(
            message="Contact information updated successfully",
            data={
                "phone": church.phone,
                "email": church.email,
                "address": church.address,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
                "updated_at": church.updated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to update contact information"
        )


def update_church_branding(
    church_id: int, branding_data: dict, db: Session
) -> SuccessResponse:
    """Update church branding"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Store branding data in documents field as JSON
        import json

        documents = json.loads(church.documents) if church.documents else {}

        if (
            "primary_color" in branding_data
            and branding_data["primary_color"] is not None
        ):
            documents["primary_color"] = branding_data["primary_color"]
        if (
            "secondary_color" in branding_data
            and branding_data["secondary_color"] is not None
        ):
            documents["secondary_color"] = branding_data["secondary_color"]

        church.documents = json.dumps(documents)
        church.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(church)

        return ResponseFactory.success(
            message="Branding updated successfully",
            data={
                "primary_color": documents.get("primary_color"),
                "secondary_color": documents.get("secondary_color"),
                "updated_at": church.updated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to update branding")


def remove_church_logo(church_id: int, db: Session) -> SuccessResponse:
    """Remove church logo"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Remove logo URL from documents field
        import json

        documents = json.loads(church.documents) if church.documents else {}
        if "logo" in documents:
            del documents["logo"]
        church.documents = json.dumps(documents)
        church.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(church)

        return ResponseFactory.success(
            message="Church logo removed successfully", data={"logo": None}
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to remove church logo")


def get_church_logo(church_id: int, db: Session) -> SuccessResponse:
    """Get church logo"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get logo URL from documents field
        import json

        documents = json.loads(church.documents) if church.documents else {}
        logo_url = documents.get("logo")

        return ResponseFactory.success(
            message="Church logo retrieved successfully", data={"logo": logo_url}
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get church logo")


def get_church_contact(church_id: int, db: Session) -> SuccessResponse:
    """Get church contact information"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        return ResponseFactory.success(
            message="Church contact information retrieved successfully",
            data={
                "phone": church.phone,
                "email": church.email,
                "address": church.address,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get church contact")


def get_church_branding(church_id: int, db: Session) -> SuccessResponse:
    """Get church branding settings"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get branding data from documents field
        import json

        documents = json.loads(church.documents) if church.documents else {}

        return ResponseFactory.success(
            message="Church branding settings retrieved successfully",
            data={
                "primary_color": documents.get("primary_color"),
                "secondary_color": documents.get("secondary_color"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get church branding")
