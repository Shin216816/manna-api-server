import logging
import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import UploadFile, File

from app.schema.donor_schema import (
    DonorProfileUpdateRequest,
    DonorPreferencesUpdateRequest
)
from app.controller.donor.invite import validate_invite_token
from app.model.m_user import User
from app.model.m_user_settings import UserSettings
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from app.utils.file_upload import upload_file, delete_file
from fastapi import HTTPException

@handle_controller_errors
def get_profile(current_user: dict, db: Session):
    """Get donor profile information"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()

    # Get user's primary church ID
    primary_church = user.get_primary_church(db)
    church_id = primary_church.id if primary_church else None

    return ResponseFactory.success(
        message="Profile retrieved successfully",
        data={
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "email": user.email,
            "phone": user.phone,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "has_password": user.has_password(),
            "church_id": church_id,
            "profile_picture_url": user.profile_picture_url,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "preferences": {
                "language": getattr(settings, 'language', 'en') if settings else "en",
                "timezone": getattr(settings, 'timezone', 'UTC') if settings else "UTC",
                "currency": getattr(settings, 'currency', 'USD') if settings else "USD",
                "theme": getattr(settings, 'theme', 'light') if settings else "light"
            }
        }
    )

@handle_controller_errors
def update_profile(data: DonorProfileUpdateRequest, current_user: dict, db: Session):
    """Update donor profile information"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields if provided
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.middle_name is not None:
        user.middle_name = data.middle_name
    if data.email is not None and data.email != user.email:
        # Check if email is already taken
        existing_user = User.get_by_email(db, data.email)
        if existing_user and existing_user.id != user.id:
            raise ValidationError("Email is already in use")
        user.email = data.email
        user.is_email_verified = False  # Require re-verification
    if data.phone is not None and data.phone != user.phone:
        # Handle empty string as None (no phone number)
        phone_to_set = data.phone.strip() if data.phone else None
        phone_to_set = phone_to_set if phone_to_set else None  # Convert empty string to None
        
        # Only check for duplicates if phone is not empty/None
        if phone_to_set:
            existing_user = User.get_by_phone(db, phone_to_set)
            if existing_user and existing_user.id != user.id:
                raise ValidationError("Phone number is already in use")
        
        user.phone = phone_to_set
        user.is_phone_verified = False if phone_to_set else False  # Require re-verification if phone is set

    # Handle church association
    if data.church_id is not None:
        if data.church_id == 0:  # Allow 0 to clear church association
            user.church_id = None
        else:
            # Verify church exists
            from app.model.m_church import Church
            church = db.query(Church).filter(Church.id == data.church_id).first()
            if church:
                user.church_id = data.church_id
            else:
                raise ValidationError(f"Church with ID {data.church_id} not found")

    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return ResponseFactory.success(
        message="Profile updated successfully",
        data={
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "email": user.email,
            "phone": user.phone,
            "church_id": user.church_id,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "updated_at": user.updated_at
        }
    )

@handle_controller_errors
async def upload_profile_picture(current_user: dict, db: Session, file: UploadFile):
    """Upload donor profile picture"""
    
    
    
    
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        
        raise HTTPException(status_code=404, detail="User not found")


    # Validate file type
    
    if not file.content_type or not file.content_type.startswith('image/'):
        
        raise ValidationError("File must be an image")

    

    # Validate file size (max 5MB)
    
    file_content = await file.read()
    file_size = len(file_content)
    
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        
        raise ValidationError("File size must be less than 5MB")

    

    # Reset file pointer for upload_file function
    
    await file.seek(0)
    

    try:
        # Upload file using the existing upload_file function
        
        upload_result = upload_file(file, file_type="profile_image")
        
        
        # Update user's profile picture URL
        
        old_url = user.profile_picture_url
        user.profile_picture_url = upload_result["url"]
        user.updated_at = datetime.now(timezone.utc)
        
        
        db.commit()
        

        response_data = {
            "profile_picture_url": upload_result["url"],
            "updated_at": user.updated_at
        }
        

        return ResponseFactory.success(
            message="Profile picture uploaded successfully",
            data=response_data
        )
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

@handle_controller_errors
def delete_profile_picture(current_user: dict, db: Session):
    """Delete donor profile picture"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.profile_picture_url:
        return ResponseFactory.success(
            message="No profile picture to delete"
        )

    try:
        # Delete file from storage
        delete_file(user.profile_picture_url)
        
        # Update user profile picture URL
        user.profile_picture_url = None
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Profile picture deleted successfully",
            data={
                "profile_picture_url": None,
                "updated_at": user.updated_at
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete profile picture")

@handle_controller_errors
def update_preferences(data: DonorPreferencesUpdateRequest, current_user: dict, db: Session):
    """Update donor preferences"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get or create user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    
    if not settings:
        settings = UserSettings(
            user_id=user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(settings)

    # Update preferences
    if data.language is not None:
        if data.language not in ["en", "es", "fr"]:
            raise ValidationError("Language must be 'en', 'es', or 'fr'")
        setattr(settings, 'language', data.language)
    
    if data.timezone is not None:
        setattr(settings, 'timezone', data.timezone)
    
    if data.currency is not None:
        if data.currency not in ["USD", "EUR", "GBP", "CAD"]:
            raise ValidationError("Currency must be 'USD', 'EUR', 'GBP', or 'CAD'")
        setattr(settings, 'currency', data.currency)
    
    if data.theme is not None:
        if data.theme not in ["light", "dark", "auto"]:
            raise ValidationError("Theme must be 'light', 'dark', or 'auto'")
        setattr(settings, 'theme', data.theme)

    # Update notification preferences
    if data.email_notifications is not None:
        setattr(settings, 'email_notifications', data.email_notifications)
    
    if data.sms_notifications is not None:
        setattr(settings, 'sms_notifications', data.sms_notifications)
    
    if data.push_notifications is not None:
        setattr(settings, 'push_notifications', data.push_notifications)

    setattr(settings, 'updated_at', datetime.now(timezone.utc))
    db.commit()
    db.refresh(settings)

    return ResponseFactory.success(
        message="Preferences updated successfully",
        data={
            "language": getattr(settings, 'language', 'en'),
            "timezone": getattr(settings, 'timezone', 'UTC'),
            "currency": getattr(settings, 'currency', 'USD'),
            "theme": getattr(settings, 'theme', 'light'),
            "email_notifications": getattr(settings, 'email_notifications', True),
            "sms_notifications": getattr(settings, 'sms_notifications', False),
            "push_notifications": getattr(settings, 'push_notifications', True),
            "updated_at": getattr(settings, 'updated_at', datetime.now(timezone.utc))
        }
    )

@handle_controller_errors
def get_profile_stats(current_user: dict, db: Session):
    """Get donor profile statistics and achievements"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate profile completion percentage
    profile_fields = [
        user.first_name, user.last_name, user.email, user.phone,
        user.is_email_verified, user.is_phone_verified, getattr(user, 'profile_picture_url', None)
    ]
    
    completed_fields = sum(1 for field in profile_fields if field is not None and field != "")
    profile_completion = (completed_fields / len(profile_fields)) * 100

    # Get account age
    account_age_days = (datetime.now(timezone.utc) - user.created_at).days

    # Get verification status
    verification_status = {
        "email_verified": user.is_email_verified,
        "phone_verified": user.is_phone_verified,
        "fully_verified": user.is_email_verified and user.is_phone_verified
    }

    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()

    return ResponseFactory.success(
        message="Profile statistics retrieved successfully",
        data={
            "profile_completion": round(profile_completion, 1),
            "account_age_days": account_age_days,
            "verification_status": verification_status,
            "preferences": {
                "language": getattr(settings, 'language', 'en') if settings else "en",
                "timezone": getattr(settings, 'timezone', 'UTC') if settings else "UTC",
                "currency": getattr(settings, 'currency', 'USD') if settings else "USD",
                "theme": getattr(settings, 'theme', 'light') if settings else "light"
            },
            "last_updated": user.updated_at
        }
    )

@handle_controller_errors
def export_profile_data(current_user: dict, db: Session):
    """Export donor profile data"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()

    # Get user's primary church ID
    primary_church = user.get_primary_church(db)
    church_id = primary_church.id if primary_church else None

    # Prepare export data
    export_data = {
        "profile": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "email": user.email,
            "phone": user.phone,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "church_id": church_id,
            "profile_picture_url": user.profile_picture_url,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "updated_at": user.updated_at
        },
        "preferences": {
            "language": getattr(settings, 'language', 'en') if settings else "en",
            "timezone": getattr(settings, 'timezone', 'UTC') if settings else "UTC",
            "currency": getattr(settings, 'currency', 'USD') if settings else "USD",
            "theme": getattr(settings, 'theme', 'light') if settings else "light"
        },
        "export_date": datetime.now(timezone.utc).isoformat(),
        "export_format": "json"
    }

    return ResponseFactory.success(
        message="Profile data exported successfully",
        data=export_data
    )

@handle_controller_errors
def deactivate_account(current_user: dict, db: Session):
    """Deactivate donor account"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark user as inactive
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    
    # Mark user settings as inactive
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings:
        settings.is_active = False
        settings.updated_at = datetime.now(timezone.utc)
    
    db.commit()

    return ResponseFactory.success(
        message="Account deactivated successfully",
        data={
            "deactivated_at": user.updated_at,
            "user_id": user.id
        }
    )

@handle_controller_errors
def reactivate_account(current_user: dict, db: Session):
    """Reactivate donor account"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark user as active
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    
    # Mark user settings as active
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings:
        settings.is_active = True
        settings.updated_at = datetime.now(timezone.utc)
    
    db.commit()

    return ResponseFactory.success(
        message="Account reactivated successfully",
        data={
            "reactivated_at": user.updated_at,
            "user_id": user.id
        }
    )

@handle_controller_errors
def associate_church(invite_token: str, current_user: dict, db: Session):
    """Associate OAuth user with a church using invite token"""
    
    user = User.get_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user already has a church association
    if user.church_id:
        raise ValidationError("User is already associated with a church")
    
    # Validate invite token and get church_id
    try:
        invite_data = validate_invite_token(invite_token)
        church_id = invite_data["church_id"]
    except Exception as e:
        raise ValidationError(f"Invalid invite token: {str(e)}")
    
    # Associate user with church
    user.church_id = church_id
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    # Update Stripe customer metadata if user has Stripe customer ID
    if user.stripe_customer_id:
        try:
            import stripe
            from app.config import config
            stripe.api_key = config.STRIPE_SECRET_KEY
            
            stripe.Customer.modify(
                user.stripe_customer_id,
                metadata={
                    'user_id': user.id,
                    'church_id': church_id,
                    'user_type': 'donor'
                }
            )
        except Exception as e:
            pass
            
    
    return ResponseFactory.success(
        message="Successfully associated with church",
        data={
            "user_id": user.id,
            "church_id": church_id,
            "updated_at": user.updated_at
        }
    )
