import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.model.m_user import User
from app.model.m_consents import Consent
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException


@handle_controller_errors
def accept_consent(current_user: dict, data, db: Session):
    """Accept consent and authorizations for donor"""

    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        consents = data.get("consents", {})
        ip_address = data.get("ip_address")
        user_agent = data.get("user_agent")

        required_consents = ["transactionRead", "charging", "dataUsage"]
        for consent_type in required_consents:
            if not consents.get(consent_type):
                raise ValidationError(f"Consent for {consent_type} is required")

        # Check if user already has a consent record
        existing_consent = db.query(Consent).filter(Consent.user_id == user.id).first()

        if existing_consent:
            # Update existing consent instead of creating new one
            existing_consent.version = "1.0"
            existing_consent.accepted_at = datetime.now(timezone.utc)
            existing_consent.ip = ip_address
            existing_consent.user_agent = user_agent
            existing_consent.text_snapshot = str(consents)

            db.commit()
            db.refresh(existing_consent)

            return ResponseFactory.success(
                message="Consent updated successfully",
                data={
                    "consent_id": existing_consent.id,
                    "version": existing_consent.version,
                    "accepted_at": existing_consent.accepted_at.isoformat(),
                    "action": "updated",
                },
            )
        else:
            # Create new consent if none exists
            consent = Consent(
                user_id=user.id,
                version="1.0",
                ip=ip_address,
                user_agent=user_agent,
                text_snapshot=str(consents),
            )

            db.add(consent)
            db.commit()
            db.refresh(consent)

            return ResponseFactory.success(
                message="Consent accepted successfully",
                data={
                    "consent_id": consent.id,
                    "version": consent.version,
                    "accepted_at": consent.accepted_at.isoformat(),
                    "action": "created",
                },
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to accept consent")


@handle_controller_errors
def get_consent_status(current_user: dict, db: Session):
    """Get donor's consent status"""

    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    latest_consent = (
        db.query(Consent)
        .filter(Consent.user_id == user.id)
        .order_by(Consent.accepted_at.desc())
        .first()
    )

    return ResponseFactory.success(
        message="Consent status retrieved successfully",
        data={
            "has_consent": latest_consent is not None,
            "consent_version": latest_consent.version if latest_consent else None,
            "accepted_at": (
                latest_consent.accepted_at.isoformat() if latest_consent else None
            ),
        },
    )


@handle_controller_errors
def get_consent_history(current_user: dict, db: Session):
    """Get donor's consent history"""

    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    consents = (
        db.query(Consent)
        .filter(Consent.user_id == user.id)
        .order_by(Consent.accepted_at.desc())
        .all()
    )

    return ResponseFactory.success(
        message="Consent history retrieved successfully",
        data={
            "consents": [
                {
                    "id": consent.id,
                    "version": consent.version,
                    "accepted_at": consent.accepted_at.isoformat(),
                    "ip": consent.ip,
                    "user_agent": consent.user_agent,
                }
                for consent in consents
            ],
            "total_count": len(consents),
        },
    )


@handle_controller_errors
def cleanup_duplicate_consents(current_user: dict, db: Session):
    """Clean up duplicate consents for the current user (admin function)"""

    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise UserNotFoundError(details={"message": "User not found"})

    try:
        # Get all consents for the user
        all_consents = (
            db.query(Consent)
            .filter(Consent.user_id == user.id)
            .order_by(Consent.accepted_at.desc())
            .all()
        )

        if len(all_consents) <= 1:
            return ResponseFactory.success(
                message="No duplicate consents found",
                data={"consents_count": len(all_consents)},
            )

        # Keep only the most recent consent
        latest_consent = all_consents[0]
        consents_to_delete = all_consents[1:]

        # Delete older consents
        for consent in consents_to_delete:
            db.delete(consent)

        db.commit()

        return ResponseFactory.success(
            message="Duplicate consents cleaned up successfully",
            data={
                "kept_consent_id": latest_consent.id,
                "deleted_count": len(consents_to_delete),
                "remaining_count": 1,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to cleanup duplicate consents"
        )
