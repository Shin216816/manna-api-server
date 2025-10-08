from fastapi import HTTPException, UploadFile
import logging
import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from app.model.m_user import User
from app.core.responses import ResponseFactory
from app.utils.security import hash_password, verify_password, generate_access_code
from app.utils.send_email import send_email_with_sendgrid
from app.utils.send_sms import send_otp_sms
from app.model.m_access_codes import AccessCode
from app.config import config


def get_mobile_profile(user_id: int, db: Session):
    """Get user profile for mobile app with church information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get church information if user is associated with a church
        church_data = None
        primary_church = user.get_primary_church(db)
        if primary_church:
            church_data = {
                "id": primary_church.id,
                "name": primary_church.name,
                "address": primary_church.address or "",
                "city": getattr(primary_church, 'city', '') or "",
                "state": getattr(primary_church, 'state', '') or "",
                "phone": primary_church.phone or "",
                "email": primary_church.email or "",
                "website": primary_church.website or "",
                "kyc_status": getattr(primary_church, 'kyc_status', 'not_submitted') or "not_submitted",
                "is_active": primary_church.is_active,
                "is_verified": getattr(primary_church, 'kyc_status', 'not_submitted') == 'approved',
                "type": "church"
            }

        church_id = primary_church.id if primary_church else None

        profile_data = {
            "id": user.id,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "church_id": church_id,  # Backward compatibility
            "church_ids": [church_id] if church_id else [],  # Mobile app expects array
            "primary_church_id": church_id,  # Mobile app expects this field
            "profile_picture_url": user.profile_picture_url,
            "role": user.role or "user",
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }

        # Include church data if available
        if church_data:
            profile_data["church"] = church_data

        
        
        
        
        
        return ResponseFactory.success(
            message="Profile retrieved successfully",
            data={
                "user": profile_data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get profile")


def update_mobile_profile(user_id: int, profile_data: Dict[str, Any], db: Session):
    """Update user profile for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update allowed fields
        if "first_name" in profile_data:
            user.first_name = profile_data["first_name"]
        if "middle_name" in profile_data:
            user.middle_name = profile_data["middle_name"]
        if "last_name" in profile_data:
            user.last_name = profile_data["last_name"]
        if "email" in profile_data and profile_data["email"] != user.email:
            # Email change requires verification
            user.email = profile_data["email"]
            user.is_email_verified = False
        if "phone" in profile_data and profile_data["phone"] != user.phone:
            # Phone change requires verification
            user.phone = profile_data["phone"]
            user.is_phone_verified = False
        
        # Handle additional fields that may be sent by mobile app but not stored in User model
        # These are ignored for now but could be stored in user preferences or metadata
        additional_fields = ["bio", "timezone", "language", "currency"]
        for field in additional_fields:
            if field in profile_data:
                # Log that these fields were received but not processed
                # In a production system, these could be stored in a user_preferences table
                pass

        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

        # Prepare user data in the format expected by mobile app
        # Get user's primary church ID
        primary_church = user.get_primary_church(db)
        church_id = primary_church.id if primary_church else None

        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "name": f"{user.first_name or ''} {user.middle_name or ''} {user.last_name or ''}".strip(),
            "email": user.email,
            "phone": user.phone,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "church_id": church_id,
            "church_ids": [church_id] if church_id else [],
            "primary_church_id": church_id,
            "profile_picture_url": user.profile_picture_url,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }

        return ResponseFactory.success(
            message="Profile updated successfully",
            data={
                "user": user_data  # Wrap user data in 'user' object for mobile app compatibility
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to update profile")


async def upload_mobile_profile_image(user_id: int, image_file: UploadFile, db: Session):
    """Upload profile image for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if image_file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Check file size (max 10MB)
        file_size = len(await image_file.read())
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Reset file pointer
        await image_file.seek(0)
        
        # Create upload directory if it doesn't exist
        upload_dir = "uploads/profile_images"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = image_file.filename.split(".")[-1]
        filename = f"user_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await image_file.read()
            buffer.write(content)
        
        # Update user profile picture URL
        user.profile_picture_url = f"/uploads/profile_images/{filename}"
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Profile image uploaded successfully",
            data={
                "profile_picture_url": user.profile_picture_url,
                "file_size": file_size,
                "filename": filename
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to upload profile image")


async def remove_mobile_profile_image(user_id: int, db: Session):
    """Remove profile image for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove file if it exists
        if user.profile_picture_url:
            try:
                file_path = user.profile_picture_url.replace("/", os.sep)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                pass
                

        # Update user
        user.profile_picture_url = None
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Profile image removed successfully",
            data={"profile_picture_url": None}
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to remove profile image")


def send_email_verification(user_id: int, db: Session):
    """Send email verification code"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.email:
            raise HTTPException(status_code=400, detail="No email address found")

        if user.is_email_verified:
            return ResponseFactory.success(
                message="Email already verified",
                data={"is_verified": True}
            )
        
        # Clean up existing codes
        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user_id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()

        # Generate new verification code
        access_code = generate_access_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        code_record = AccessCode(
            user_id=user_id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()

        # Send verification email
        try:
            send_email_with_sendgrid(
                to_email=user.email,
                subject="Verify Your Email - Manna",
                body_html=f"""
                <h2>Email Verification</h2>
                <p>Your verification code is: <strong>{access_code}</strong></p>
                <p>This code will expire in 5 minutes.</p>
                """
            )
        except Exception as e:
            
            raise HTTPException(status_code=500, detail="Failed to send verification email")

        return ResponseFactory.success(
            message="Verification code sent successfully",
            data={
                "email": user.email,
                "expires_at": expires_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to send email verification")


def confirm_email_verification(user_id: int, code: str, email: str, db: Session):
    """Confirm email verification"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.email != email:
            raise HTTPException(status_code=400, detail="Email mismatch")
        
        # Check verification code
        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user_id,
            AccessCode.access_code == code,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not access_code:
            raise HTTPException(status_code=400, detail="Invalid or expired code")

        # Mark email as verified
        user.is_email_verified = True
        user.updated_at = datetime.now(timezone.utc)
        
        # Remove verification code
        db.delete(access_code)
        db.commit()

        return ResponseFactory.success(
            message="Email verified successfully",
            data={
                "is_email_verified": True,
                "email": user.email
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to confirm email verification")


def send_phone_verification(user_id: int, db: Session):
    """Send phone verification code"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.phone:
            raise HTTPException(status_code=400, detail="No phone number found")

        if user.is_phone_verified:
            return ResponseFactory.success(
                message="Phone already verified",
                data={"is_verified": True}
            )
        
        # Clean up existing codes
        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user_id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()

        # Generate new verification code
        access_code = generate_access_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        code_record = AccessCode(
            user_id=user_id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()

        # Send verification SMS
        try:
            send_otp_sms(user.phone, access_code)
        except Exception as e:
            
            raise HTTPException(status_code=500, detail="Failed to send verification SMS")

        return ResponseFactory.success(
            message="Verification code sent successfully",
            data={
                "phone": user.phone,
                "expires_at": expires_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to send phone verification")


def confirm_phone_verification(user_id: int, code: str, phone: str, db: Session):
    """Confirm phone verification"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.phone != phone:
            raise HTTPException(status_code=400, detail="Phone number mismatch")
        
        # Check verification code
        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user_id,
            AccessCode.access_code == code,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not access_code:
            raise HTTPException(status_code=400, detail="Invalid or expired code")

        # Mark phone as verified
        user.is_phone_verified = True
        user.updated_at = datetime.now(timezone.utc)
        
        # Remove verification code
        db.delete(access_code)
        db.commit()

        return ResponseFactory.success(
            message="Phone verified successfully",
            data={
                "is_phone_verified": True,
                "phone": user.phone
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to confirm phone verification")
