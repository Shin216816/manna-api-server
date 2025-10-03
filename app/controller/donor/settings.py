"""
Donor Settings Controller

Handles donor settings management including:
- Roundup frequency and multiplier settings
- Monthly caps and pause functionality
- Processing fee preferences
- Notification preferences
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.model.m_donation_preference import DonationPreference
from app.model.m_user import User
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException


@handle_controller_errors
def get_donor_settings(user_id: int, db: Session) -> ResponseFactory:
    """Get donor settings for the current user"""
    try:
        # Get or create donation preferences
        settings = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not settings:
            # Create default settings
            settings = DonationPreference(
                user_id=user_id,
                frequency="biweekly",
                multiplier="1x",
                monthly_cap=None,
                pause=False,
                cover_processing_fees=False,
                auto_collect=True,
                email_notifications=True,
                sms_notifications=False,
                collection_reminders=True,
                share_impact_data=True,
                anonymous_donations=False
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return ResponseFactory.success(
            message="Donor settings retrieved successfully",
            data={
                "id": settings.id,
                "user_id": settings.user_id,
                "roundup_settings": {
                    "frequency": settings.frequency,
                    "multiplier": settings.multiplier,
                    "monthly_cap": float(settings.monthly_cap) if settings.monthly_cap else None,
                    "pause_giving": settings.pause
                },
                "processing_settings": {
                    "cover_processing_fees": settings.cover_processing_fees,
                    "auto_collect": settings.auto_collect
                },
                "notification_settings": {
                    "email_notifications": settings.email_notifications,
                    "sms_notifications": settings.sms_notifications,
                    "collection_reminders": settings.collection_reminders
                },
                "privacy_settings": {
                    "share_impact_data": settings.share_impact_data,
                    "anonymous_donations": settings.anonymous_donations
                },
                "created_at": settings.created_at.isoformat(),
                "updated_at": settings.updated_at.isoformat()
            }
        )

    except Exception as e:
        logging.error(f"Error getting donor settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get donor settings")


@handle_controller_errors
def update_donor_settings(
    user_id: int, 
    settings_data: dict, 
    db: Session
) -> ResponseFactory:
    """Update donor settings for the current user"""
    try:
        # Get existing settings
        settings = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not settings:
            # Create new settings
            settings = DonationPreference(user_id=user_id)
            db.add(settings)

        # Update roundup settings
        if "frequency" in settings_data:
            if settings_data["frequency"] not in ["biweekly", "monthly"]:
                raise ValidationError("Frequency must be 'biweekly' or 'monthly'")
            settings.frequency = settings_data["frequency"]

        if "multiplier" in settings_data:
            multiplier = settings_data["multiplier"]
            if not multiplier.endswith('x') or not multiplier[:-1].replace('.', '').isdigit():
                raise ValidationError("Multiplier must be in format like '1x', '2x', '1.5x'")
            settings.multiplier = multiplier

        if "monthly_cap" in settings_data:
            monthly_cap = settings_data["monthly_cap"]
            if monthly_cap is not None and (not isinstance(monthly_cap, (int, float)) or monthly_cap < 0):
                raise ValidationError("Monthly cap must be a positive number or null")
            settings.monthly_cap = monthly_cap

        if "pause_giving" in settings_data:
            settings.pause = bool(settings_data["pause_giving"])

        # Update processing settings
        if "cover_processing_fees" in settings_data:
            settings.cover_processing_fees = bool(settings_data["cover_processing_fees"])

        if "auto_collect" in settings_data:
            settings.auto_collect = bool(settings_data["auto_collect"])

        # Update notification settings
        if "email_notifications" in settings_data:
            settings.email_notifications = bool(settings_data["email_notifications"])

        if "sms_notifications" in settings_data:
            settings.sms_notifications = bool(settings_data["sms_notifications"])

        if "collection_reminders" in settings_data:
            settings.collection_reminders = bool(settings_data["collection_reminders"])

        # Update privacy settings
        if "share_impact_data" in settings_data:
            settings.share_impact_data = bool(settings_data["share_impact_data"])

        if "anonymous_donations" in settings_data:
            settings.anonymous_donations = bool(settings_data["anonymous_donations"])

        settings.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Donor settings updated successfully",
            data={
                "id": settings.id,
                "user_id": settings.user_id,
                "roundup_settings": {
                    "frequency": settings.frequency,
                    "multiplier": settings.multiplier,
                    "monthly_cap": float(settings.monthly_cap) if settings.monthly_cap else None,
                    "pause_giving": settings.pause
                },
                "processing_settings": {
                    "cover_processing_fees": settings.cover_processing_fees,
                    "auto_collect": settings.auto_collect
                },
                "notification_settings": {
                    "email_notifications": settings.email_notifications,
                    "sms_notifications": settings.sms_notifications,
                    "collection_reminders": settings.collection_reminders
                },
                "privacy_settings": {
                    "share_impact_data": settings.share_impact_data,
                    "anonymous_donations": settings.anonymous_donations
                },
                "updated_at": settings.updated_at.isoformat()
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error updating donor settings: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update donor settings")


@handle_controller_errors
def pause_giving(user_id: int, db: Session) -> ResponseFactory:
    """Pause roundup giving for the current user"""
    try:
        settings = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not settings:
            settings = DonationPreference(user_id=user_id, pause=True)
            db.add(settings)
        else:
            settings.pause = True
            settings.updated_at = datetime.now(timezone.utc)

        db.commit()

        return ResponseFactory.success(
            message="Giving paused successfully",
            data={
                "pause_giving": True,
                "paused_at": datetime.now(timezone.utc).isoformat()
            }
        )

    except Exception as e:
        logging.error(f"Error pausing giving: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to pause giving")


@handle_controller_errors
def resume_giving(user_id: int, db: Session) -> ResponseFactory:
    """Resume roundup giving for the current user"""
    try:
        settings = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not settings:
            settings = DonationPreference(user_id=user_id, pause=False)
            db.add(settings)
        else:
            settings.pause = False
            settings.updated_at = datetime.now(timezone.utc)

        db.commit()

        return ResponseFactory.success(
            message="Giving resumed successfully",
            data={
                "pause_giving": False,
                "resumed_at": datetime.now(timezone.utc).isoformat()
            }
        )

    except Exception as e:
        logging.error(f"Error resuming giving: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to resume giving")


@handle_controller_errors
def get_roundup_preview(user_id: int, db: Session) -> ResponseFactory:
    """Get preview of roundup settings and estimated impact"""
    try:
        settings = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        
        if not settings:
            settings = DonationPreference(user_id=user_id)
            db.add(settings)
            db.commit()

        # Calculate estimated monthly impact
        multiplier = float(settings.multiplier.replace('x', '')) if settings.multiplier else 1.0
        
        # This would typically calculate based on historical transaction data
        # For now, we'll provide a placeholder calculation
        estimated_monthly_roundup = 25.0 * multiplier  # Placeholder calculation
        
        # Apply monthly cap if set
        if settings.monthly_cap and estimated_monthly_roundup > settings.monthly_cap:
            estimated_monthly_roundup = settings.monthly_cap

        return ResponseFactory.success(
            message="Roundup preview retrieved successfully",
            data={
                "current_settings": {
                    "frequency": settings.frequency,
                    "multiplier": settings.multiplier,
                    "monthly_cap": float(settings.monthly_cap) if settings.monthly_cap else None,
                    "pause_giving": settings.pause
                },
                "estimated_impact": {
                    "monthly_roundup": round(estimated_monthly_roundup, 2),
                    "annual_roundup": round(estimated_monthly_roundup * 12, 2),
                    "frequency_description": f"Every {settings.frequency}" if settings.frequency else "Not set"
                },
                "next_collection": "Calculated based on frequency"  # This would be calculated based on last collection
            }
        )

    except Exception as e:
        logging.error(f"Error getting roundup preview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get roundup preview")