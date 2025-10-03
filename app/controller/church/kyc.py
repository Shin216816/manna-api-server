from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any

from app.model.m_church import Church
from app.model.m_audit_log import AuditLog
from app.services.kyc_service import KYCService
from app.core.responses import ResponseFactory, SuccessResponse
from app.core.exceptions import StripeError


def init_kyc(church_id: int, db: Session) -> SuccessResponse:
    """Initialize KYC process by creating Stripe Connect account"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if church.kyc_state != "REGISTERED":
            raise HTTPException(
                status_code=400,
                detail=f"Church is in {church.kyc_state} state, cannot initialize KYC",
            )

        # Create Stripe Connect account
        result = KYCService.create_stripe_connect_account(church, db)

        return ResponseFactory.success(
            message="KYC initialization successful", data=result
        )

    except HTTPException:
        raise
    except StripeError as e:

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to initialize KYC")


def generate_kyc_link(church_id: int, db: Session) -> SuccessResponse:
    """Generate a fresh onboarding link for KYC completion"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if not church.stripe_account_id:
            raise HTTPException(
                status_code=400,
                detail="No Stripe account found. Please initialize KYC first.",
            )

        # Generate onboarding link
        onboarding_url = KYCService.generate_onboarding_link(church, db)

        return ResponseFactory.success(
            message="Onboarding link generated successfully",
            data={"onboarding_url": onboarding_url, "kyc_state": church.kyc_state},
        )

    except HTTPException:
        raise
    except StripeError as e:

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to generate onboarding link"
        )


def get_kyc_status(church_id: int, db: Session) -> SuccessResponse:
    """Get current KYC status and sync with Stripe"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Sync status with Stripe
        status_data = KYCService.sync_stripe_account_status(church, db)

        return ResponseFactory.success(
            message="KYC status retrieved successfully", data=status_data
        )

    except HTTPException:
        raise
    except StripeError as e:

        # Return current status even if Stripe sync fails
        return ResponseFactory.success(
            message="KYC status retrieved (Stripe sync failed)",
            data={
                "kyc_state": church.kyc_state,
                "charges_enabled": church.charges_enabled,
                "payouts_enabled": church.payouts_enabled,
                "disabled_reason": church.disabled_reason,
            },
        )
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get KYC status")


def get_payouts_status(church_id: int, db: Session) -> SuccessResponse:
    """Get payouts status - locked until ACTIVE state"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Check if payouts are enabled
        if church.kyc_state != "ACTIVE":
            return ResponseFactory.success(
                message="Payouts not available",
                data={
                    "payouts_enabled": False,
                    "kyc_state": church.kyc_state,
                    "message": "Payouts will be available once KYC is complete and verified",
                },
            )

        return ResponseFactory.success(
            message="Payouts status retrieved successfully",
            data={
                "payouts_enabled": church.payouts_enabled,
                "kyc_state": church.kyc_state,
                "stripe_account_id": church.stripe_account_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get payouts status")
