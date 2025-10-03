"""
Stripe Identity Service for KYC verification
Handles identity verification for church admins who need to receive payouts
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.model.m_church_admin import ChurchAdmin
from app.model.m_audit_log import AuditLog
from app.utils.stripe_client import stripe
from app.config import config


class StripeIdentityService:
    """Service for handling Stripe Identity verification for church admins"""

    @staticmethod
    def create_verification_session(
        church_admin_id: int, db: Session
    ) -> Dict[str, Any]:
        """Create a new Stripe Identity verification session for a church admin"""
        try:
            # Get church admin
            church_admin = db.query(ChurchAdmin).filter_by(id=church_admin_id).first()
            if not church_admin:
                raise ValueError(f"Church admin {church_admin_id} not found")

            # Check if user exists
            if not church_admin.user:
                raise ValueError(f"User not found for church admin {church_admin_id}")

            user = church_admin.user

            # Create verification session
            verification_session = stripe.identity.VerificationSession.create(
                type="document",
                return_url=f"{config.ADMIN_FRONTEND_URL}/church/kyc/complete",
                metadata={
                    "church_admin_id": str(church_admin_id),
                    "user_id": str(user.id),
                    "church_id": str(church_admin.church_id),
                },
            )

            # Update church admin with verification session ID
            church_admin.stripe_identity_session_id = verification_session.id
            church_admin.identity_verification_status = "pending"
            church_admin.updated_at = datetime.now(timezone.utc)

            # Commit church admin changes
            db.commit()
            db.refresh(church_admin)

            # Log the action
            audit_log = AuditLog(
                actor_type="user",
                actor_id=user.id,
                action="IDENTITY_VERIFICATION_STARTED",
                details_json={
                    "stripe_session_id": verification_session.id,
                    "verification_type": "document",
                    "church_admin_id": church_admin_id,
                    "church_id": church_admin.church_id,
                    "user_email": user.email,
                    "user_phone": user.phone,
                },
            )
            db.add(audit_log)
            db.commit()

            return {
                "session_id": verification_session.id,
                "client_secret": verification_session.client_secret,
                "url": verification_session.url,
                "status": "pending",
            }

        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(
                f"Failed to create verification session: {str(e)}"
            )
        except Exception as e:
            raise stripe.error.StripeError(
                f"Failed to create verification session: {str(e)}"
            )

    @staticmethod
    def check_verification_status(church_admin_id: int, db: Session) -> Dict[str, Any]:
        """Check the verification status of a church admin's Stripe Identity session"""
        try:
            # Get church admin
            church_admin = db.query(ChurchAdmin).filter_by(id=church_admin_id).first()
            if not church_admin:
                raise ValueError(f"Church admin {church_admin_id} not found")

            if not church_admin.stripe_identity_session_id:
                return {
                    "status": "not_started",
                    "message": "No verification session found",
                }

            # Retrieve verification session from Stripe
            verification_session = stripe.identity.VerificationSession.retrieve(
                church_admin.stripe_identity_session_id
            )

            # Update church admin verification status based on Stripe response
            previous_status = church_admin.identity_verification_status
            new_status = verification_session.status

            if new_status != previous_status:
                church_admin.identity_verification_status = new_status
                church_admin.updated_at = datetime.now(timezone.utc)

                # Set verification date if completed
                if new_status == "verified":
                    church_admin.identity_verification_date = datetime.now(timezone.utc)

                # Commit changes
                db.commit()
                db.refresh(church_admin)

                # Log status change
                audit_log = AuditLog(
                    actor_type="webhook",
                    actor_id=church_admin.user_id,
                    action="IDENTITY_VERIFICATION_STATUS_CHANGED",
                    details_json={
                        "stripe_session_id": church_admin.stripe_identity_session_id,
                        "church_admin_id": church_admin_id,
                        "church_id": church_admin.church_id,
                        "previous_status": previous_status,
                        "new_status": new_status,
                        "verification_date": (
                            church_admin.identity_verification_date.isoformat()
                            if church_admin.identity_verification_date
                            else None
                        ),
                    },
                )
                db.add(audit_log)
                db.commit()

            return {
                "status": new_status,
                "session_id": church_admin.stripe_identity_session_id,
                "verification_date": (
                    church_admin.identity_verification_date.isoformat()
                    if church_admin.identity_verification_date
                    else None
                ),
            }

        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(
                f"Failed to check verification status: {str(e)}"
            )
        except Exception as e:
            raise stripe.error.StripeError(
                f"Failed to check verification status: {str(e)}"
            )

    @staticmethod
    def cancel_verification_session(
        church_admin_id: int, db: Session
    ) -> Dict[str, Any]:
        """Cancel a Stripe Identity verification session for a church admin"""
        try:
            # Get church admin
            church_admin = db.query(ChurchAdmin).filter_by(id=church_admin_id).first()
            if not church_admin:
                raise ValueError(f"Church admin {church_admin_id} not found")

            if not church_admin.stripe_identity_session_id:
                return {
                    "status": "not_started",
                    "message": "No verification session found",
                }

            # Cancel verification session in Stripe
            verification_session = stripe.identity.VerificationSession.cancel(
                church_admin.stripe_identity_session_id
            )

            # Update church admin status
            church_admin.identity_verification_status = "cancelled"
            church_admin.updated_at = datetime.now(timezone.utc)

            # Commit changes
            db.commit()
            db.refresh(church_admin)

            # Log the action
            audit_log = AuditLog(
                actor_type="user",
                actor_id=church_admin.user_id,
                action="IDENTITY_VERIFICATION_CANCELLED",
                details_json={
                    "stripe_session_id": church_admin.stripe_identity_session_id,
                    "church_admin_id": church_admin_id,
                    "church_id": church_admin.church_id,
                },
            )
            db.add(audit_log)
            db.commit()

            return {
                "status": "cancelled",
                "session_id": church_admin.stripe_identity_session_id,
            }

        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(
                f"Failed to cancel verification session: {str(e)}"
            )
        except Exception as e:
            raise stripe.error.StripeError(
                f"Failed to cancel verification session: {str(e)}"
            )

    @staticmethod
    def get_verification_info(church_admin_id: int, db: Session) -> Dict[str, Any]:
        """Get verification information for a church admin"""
        try:
            # Get church admin
            church_admin = db.query(ChurchAdmin).filter_by(id=church_admin_id).first()
            if not church_admin:
                raise ValueError(f"Church admin {church_admin_id} not found")

            return {
                "church_admin_id": church_admin_id,
                "church_id": church_admin.church_id,
                "verification_status": church_admin.identity_verification_status,
                "verification_date": (
                    church_admin.identity_verification_date.isoformat()
                    if church_admin.identity_verification_date
                    else None
                ),
                "session_id": church_admin.stripe_identity_session_id,
                "is_verified": (
                    church_admin.identity_verification_status == "verified"
                    and church_admin.identity_verification_date is not None
                ),
            }

        except Exception as e:
            raise ValueError(f"Failed to get verification info: {str(e)}")

    @staticmethod
    def get_verification_info_by_user_id(
        user_id: int, db: Session
    ) -> Optional[Dict[str, Any]]:
        """Get verification information for a church admin by user ID"""
        try:
            # Get church admin by user ID
            church_admin = db.query(ChurchAdmin).filter_by(user_id=user_id).first()
            if not church_admin:
                return None

            return {
                "church_admin_id": church_admin.id,
                "church_id": church_admin.church_id,
                "verification_status": church_admin.identity_verification_status,
                "verification_date": (
                    church_admin.identity_verification_date.isoformat()
                    if church_admin.identity_verification_date
                    else None
                ),
                "session_id": church_admin.stripe_identity_session_id,
                "is_verified": (
                    church_admin.identity_verification_status == "verified"
                    and church_admin.identity_verification_date is not None
                ),
            }

        except Exception as e:
            return None
