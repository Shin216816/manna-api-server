import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.schema.donor_schema import (
    DonorRegisterRequest, DonorLoginRequest, DonorLogoutRequest,
    DonorForgotPasswordRequest, DonorVerifyOtpRequest, DonorResetPasswordRequest,
    DonorGoogleOAuthRequest, DonorAppleOAuthRequest, DonorRefreshTokenRequest,
    DonorRegisterConfirmRequest, DonorRegisterCodeResendRequest,
    DonorVerifyEmailRequest, DonorVerifyPhoneRequest, DonorResendVerificationRequest,
    DonorChangePasswordRequest, DonorUpdateProfileRequest
)
from app.model.m_access_codes import AccessCode
from app.utils.security import hash_password, verify_password, generate_access_code
from app.utils.send_email import send_email_with_sendgrid
from app.utils.send_sms import send_otp_sms
from app.utils.database import get_db
from app.model.m_user import User
from app.utils.token_manager import token_manager
from app.core.exceptions import MannaException, ValidationError
from app.core.responses import ResponseFactory
from datetime import datetime, timezone
import hashlib
import logging
import secrets


def validate_invite_token(token: str, db: Session):
    """Validate an invite token and return church_id"""
    try:
        from app.model.m_church import Church
        
        # For demo purposes, accept any token and return first available church
        if not token or len(token) < 3:
            raise ValidationError("Invalid invite token")
        
        # Get first active church from database
        church = db.query(Church).filter(Church.is_active == True).first()
        if not church:
            # Create a demo church if none exists
            church = Church(
                name="Demo Church",
                address="123 Demo Street",
                city="Demo City",
                state="CA",
                zip_code="12345",
                phone="555-0123",
                email="demo@church.com",
                is_active=True,
                is_verified=True
            )
            db.add(church)
            db.commit()
            db.refresh(church)
        
        return church.id
            
    except Exception as e:
        raise ValidationError(f"Failed to validate invite token: {str(e)}")


def create_stripe_customer(user_data: dict):
    """Create Stripe customer for the new donor"""
    try:
        # Import Stripe here to avoid circular imports
        try:
            import stripe
            from app.config import config
            
            stripe.api_key = config.STRIPE_SECRET_KEY
            
            customer = stripe.Customer.create(
                email=user_data.get('email'),
                name=f"{user_data.get('first_name', '') or ''} {user_data.get('last_name', '') or ''}".strip(),
                metadata={
                    'user_id': user_data.get('id'),
                    'church_id': user_data.get('church_id'),
                    'user_type': 'donor'
                }
            )
            
            return customer.id
        except ImportError:
            # Stripe not installed - return None
            return None
        
    except Exception as e:
        # Log error but don't fail signup - Stripe customer can be created later
        
        return None


def donor_register(db: Session, user_data: dict):
    """Register a new donor user"""
    try:
        # Check if user already exists
        email = user_data.get('email')
        if email:
            existing_user = User.get_by_email(db, email)
            if existing_user:
                raise ValidationError("User with this email already exists")
        
        # Prepare user data for User model
        clean_user_data = {
            'email': user_data.get('email'),
            'phone': user_data.get('phone'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'middle_name': user_data.get('middle_name'),
            'role': 'donor',
            'church_id': user_data.get('church_id'),
            'is_active': True
        }
        
        # Handle password hashing
        password = user_data.get('password')
        if password:
            clean_user_data['password_hash'] = hash_password(password)
        
        # Create user using SQLAlchemy model
        user = User(**clean_user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return ResponseFactory.success(
            message="Donor registered successfully",
            data={
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to register donor: {str(e)}")


def donor_signup(db: Session, email: str, password: str | None = None, oauth_provider: str | None = None, invite_token: str | None = None, first_name: str | None = None, last_name: str | None = None, request=None):
    """Initiate donor signup with OTP verification using existing mobile auth logic"""
    try:
        # Validate invite token
        if not invite_token:
            raise ValidationError("Invite token is required")
        
        church_id = validate_invite_token(invite_token, db)
        
        # Check if user already exists
        existing_user = User.get_by_email(db, email)
        if existing_user:
            # Check if user is already verified
            if existing_user.is_email_verified:
                raise ValidationError("User with this email already exists")
            
            # Update existing unverified user
            user = existing_user
            user.first_name = first_name or 'Donor'
            user.last_name = last_name or 'User'
            user.password_hash = hash_password(password) if password else None
            user.role = "donor"
            user.church_id = church_id
            db.commit()
            db.refresh(user)
        else:
            # Create new user (unverified)
            user = User(
                first_name=first_name or 'Donor',
                last_name=last_name or 'User',
                email=email,
                password_hash=hash_password(password) if password else None,
                role="donor",
                church_id=church_id,
                is_email_verified=False,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Clean up any existing access codes for this user
        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user.id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()
        
        # Generate access code for verification (ensure consistent format)
        access_code = generate_access_code().upper()  # Normalize to uppercase
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Debug: Log the access code being created
        logging.info(f"Creating access code for user {user.id}: {access_code}, expires at: {expires_at}")
        
        # Create access code record using existing AccessCode model
        code_record = AccessCode(
            user_id=user.id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()
        db.refresh(code_record)
        
        # Debug: Verify the code was saved
        saved_code = db.query(AccessCode).filter(AccessCode.id == code_record.id).first()
        logging.info(f"Saved access code: {saved_code.access_code if saved_code else 'NOT FOUND'}")
        
        # Send OTP via email
        try:
            send_email_with_sendgrid(
                to_email=email,
                subject="Verify Your Manna Account",
                html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Welcome to Manna!</h2>
                    <p>Thank you for signing up. Please use the verification code below to complete your registration:</p>
                    <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #4F46E5; font-size: 32px; margin: 0; letter-spacing: 4px;">{access_code}</h1>
                    </div>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
                """
            )
        except Exception as e:
            logging.error(f"Failed to send OTP email: {str(e)}")
            # Don't fail the signup if email fails - user can still verify
        
        return ResponseFactory.success(
            message="Verification code sent successfully",
            data={
                "user_id": user.id,
                "email": email,
                "access_code": access_code,  # For development/testing
                "expires_at": expires_at.isoformat(),
                "church_id": church_id
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to initiate donor signup: {str(e)}")


def donor_confirm_registration(data, db: Session):
    """Confirm donor registration with OTP using existing mobile auth logic"""
    try:
        from app.model.m_access_codes import AccessCode
        from app.model.m_refresh_token import RefreshToken
        from app.utils.jwt_handler import create_refresh_token
        from datetime import datetime, timezone
        
        # Find user by email
        user = User.get_by_email(db, data.email)
        if not user:
            raise ValidationError("User not found")
        
        # Debug: Check what access codes exist for this user
        all_codes = db.query(AccessCode).filter(AccessCode.user_id == user.id).all()
        logging.info(f"All access codes for user {user.id}: {[(code.access_code, code.expires_at, code.expires_at > datetime.now(timezone.utc)) for code in all_codes]}")
        logging.info(f"Looking for access code: {data.access_code}")
        logging.info(f"Current time: {datetime.now(timezone.utc)}")
        
        # Find and validate access code with proper timezone handling
        current_time = datetime.now(timezone.utc)
        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.access_code.strip().upper(),  # Normalize code
            AccessCode.expires_at > current_time
        ).first()
        
        if not access_code:
            # Check if code exists but is expired
            expired_code = db.query(AccessCode).filter(
                AccessCode.user_id == user.id,
                AccessCode.access_code == data.access_code.strip().upper()
            ).first()
            if expired_code:
                raise ValidationError("Verification code has expired. Please request a new code.")
            else:
                raise ValidationError("Invalid verification code. Please check the code and try again.")
        
        # Mark user as verified
        user.is_email_verified = True
        user.updated_at = datetime.now(timezone.utc)
        
        # Clean up the used access code
        db.delete(access_code)
        db.commit()
        db.refresh(user)
        
        # Create Stripe customer
        stripe_customer_id = create_stripe_customer({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'church_id': user.church_id
        })
        
        # Update user with Stripe customer ID
        if stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
            db.commit()
        
        # Generate tokens for the verified user (following mobile auth pattern)
        access_token, jti, session_id = token_manager.create_access_token({
            "user_id": user.id,
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "church_id": user.church_id,
            "role": "donor"
        })
        
        # Create refresh token using the proper utility function (matching mobile auth)
        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)
        
        return ResponseFactory.success(
            message="Registration confirmed successfully",
            data={
                "user_id": user.id,
                "email": user.email,
                "church_id": user.church_id,
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token_obj.token,
                    "token_type": "bearer",
                    "expires_in": 3600
                }
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to confirm registration: {str(e)}")


def donor_resend_registration_code(data, db: Session):
    """Resend registration OTP code using existing mobile auth logic"""
    try:
        from app.model.m_access_codes import AccessCode
        from datetime import datetime, timezone, timedelta
        
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = db.query(User).filter(User.phone == data.phone).first()
        
        if not user:
            raise ValidationError("User not found")

        # Clean up existing access codes for this user
        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user.id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()

        # Generate new access code (ensure consistent format)
        access_code = generate_access_code().upper()  # Normalize to uppercase
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Create new access code record
        code_record = AccessCode(
            user_id=user.id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()
        db.refresh(code_record)
        
        # Debug: Log the access code being created
        logging.info(f"Creating access code for user {user.id}: {access_code}, expires at: {expires_at}")
        
        # Debug: Verify the code was saved
        saved_code = db.query(AccessCode).filter(AccessCode.id == code_record.id).first()
        logging.info(f"Saved access code: {saved_code.access_code if saved_code else 'NOT FOUND'}")
        
        # Send new OTP via email or SMS
        try:
            if data.email:
                send_email_with_sendgrid(
                    to_email=data.email,
                    subject="New Verification Code - Manna",
                    html_content=f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #333;">New Verification Code</h2>
                        <p>Here's your new verification code:</p>
                        <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0;">
                            <h1 style="color: #4F46E5; font-size: 32px; margin: 0; letter-spacing: 4px;">{access_code}</h1>
                        </div>
                        <p>This code will expire in 10 minutes.</p>
                    </div>
                    """
                )
            elif data.phone:
                send_otp_sms(
                    phone_number=data.phone,
                    otp_code=access_code
                )
        except Exception as e:
            contact_method = "email" if data.email else "SMS"
            logging.error(f"Failed to send resend OTP via {contact_method}: {str(e)}")
        
        return ResponseFactory.success(
            message="Verification code resent successfully",
            data={
                "access_code": access_code,  # For development
                "expires_at": expires_at.isoformat()
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to resend verification code: {str(e)}")


def donor_login(db: Session, email: str, password: str | None = None, oauth_provider: str | None = None, request=None):
    """Authenticate donor and return access token"""
    try:
        # Validate required fields
        if not oauth_provider and not password:
            raise ValidationError("Either password or OAuth provider is required")
        
        if not email:
            raise ValidationError("Email is required")
        
        # Find user using SQLAlchemy model
        if oauth_provider:
            user = db.query(User).filter(
                User.email == email,
                User.oauth_provider == oauth_provider,
                User.is_active == True
            ).first()
        else:
            user = db.query(User).filter(
                User.email == email,
                User.is_active == True
            ).first()
        
        if not user:
            raise ValidationError("Invalid credentials")
        
        # Verify password if not OAuth
        if not oauth_provider:
            # Password is required for non-OAuth login
            if not password:
                raise ValidationError("Password is required")
            
            # Verify the password
            if not user.verify_password(password):
                raise ValidationError("Invalid credentials")
        
        # Get church_id from user's direct church association
        church_id = user.church_id
        
        # Generate access token with proper session creation
        access_token, jti, session_id = token_manager.create_access_token({
            "user_id": user.id,
            "email": user.email,
            "church_id": church_id,
            "role": "donor"
        }, request=request)
        
        return ResponseFactory.success(
            message="Login successful",
            data={
                "user_id": user.id,
                "email": user.email,
                "church_id": church_id,
                "access_token": access_token,
                "session_id": session_id
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to authenticate donor: {str(e)}")


def donor_forgot_password(data: DonorForgotPasswordRequest, db: Session):
    """Send password reset instructions to donor"""
    try:
        email = data.email if data.email else None
        phone = data.phone if data.phone else None
        
        if not email and not phone:
            raise ValidationError("Either email or phone is required")
        
        user = None
        if email:
            user = User.get_by_email(db, email)
        if phone and not user:
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            user = User.get_by_phone(db, clean_phone)
            if not user:
                user = User.get_by_phone(db, f"+{clean_phone}")
        
        if not user:
            raise ValidationError("User not found with the provided information")

        # Ensure user is a donor
        if user.role != 'donor':
            raise ValidationError("This service is only available for donors")

        # Clean up existing access codes
        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user.id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()

        # Generate new access code
        access_code = generate_access_code().upper()  # Normalize to uppercase
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=300)  # 5 minutes

        code_record = AccessCode(
            user_id=user.id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()

        # Send OTP via email or SMS
        if email:
            send_email_with_sendgrid(
                to_email=email,
                subject="Reset your Manna password",
                body_html=f"Your password reset code is: {access_code}"
            )
        if phone:
            send_otp_sms(phone, access_code)

        return ResponseFactory.success(
            message="Password reset instructions sent successfully",
            data={
                "message": "Password reset instructions sent",
                "expires_at": expires_at.isoformat()
            }
        )

    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to send password reset: {str(e)}")


def donor_verify_otp(data: DonorVerifyOtpRequest, db: Session):
    """Verify OTP for donor password reset"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)
        
        if not user:
            raise ValidationError("User not found")

        # Ensure user is a donor
        if user.role != 'donor':
            raise ValidationError("This service is only available for donors")

        # Verify access code
        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.otp,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not access_code:
            raise ValidationError("Invalid or expired OTP")

        # Generate reset token for password change step
        reset_token = secrets.token_urlsafe(32)
        
        return ResponseFactory.success(
            message="OTP verified successfully",
            data={
                "user_id": user.id,
                "resetToken": reset_token,
                "access_code": data.otp  # Keep the access code for password reset
            }
        )

    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to verify OTP: {str(e)}")


def donor_reset_password(data: DonorResetPasswordRequest, db: Session):
    """Reset donor password with verified OTP"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)
        
        if not user:
            raise ValidationError("User not found")

        # Ensure user is a donor
        if user.role != 'donor':
            raise ValidationError("This service is only available for donors")

        # Verify access code is still valid
        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.otp,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not access_code:
            raise ValidationError("Invalid or expired OTP")

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        # Clean up access code
        db.delete(access_code)
        db.commit()

        return ResponseFactory.success(
            message="Password reset successfully"
        )

    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to reset password: {str(e)}")


def donor_change_password(data: DonorChangePasswordRequest, user_id: int, db: Session):
    """Change donor password"""
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")

        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            raise ValidationError("Current password is incorrect")

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="Password changed successfully"
        )

    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to change password: {str(e)}")


def donor_send_phone_verification(phone: str, user_id: int, db: Session):
    """Send OTP verification code to phone number - matches email verification pattern"""
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")
        
        # Validate phone number format
        clean_phone = phone.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if not clean_phone or len(clean_phone) < 10:
            raise ValidationError("Invalid phone number format")
        
        # Generate OTP code (same as email verification)
        access_code = generate_access_code().upper()  # Normalize to uppercase
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Create access code record (same structure as email verification)
        access_code_record = AccessCode(
            user_id=user_id,
            access_code=access_code,  # Use access_code field, not code
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )
        db.add(access_code_record)
        db.commit()
        db.refresh(access_code_record)
        
        # Send SMS
        try:
            send_otp_sms(phone, access_code)
        except Exception as e:
            logging.error(f"Failed to send SMS: {str(e)}")
            raise ValidationError("Failed to send verification code")
        
        return ResponseFactory.success(
            message="Verification code sent to your phone",
            data={
                "phone": phone,
                "access_code": access_code,  # For development/testing
                "expires_at": expires_at.isoformat()
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to send phone verification: {str(e)}")


def donor_verify_phone_verification(phone: str, access_code: str, user_id: int, db: Session):
    """Verify phone number using OTP code - matches email verification pattern"""
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")
        
        # Find and validate access code (same logic as email verification)
        current_time = datetime.now(timezone.utc)
        access_code_record = db.query(AccessCode).filter(
            AccessCode.user_id == user_id,
            AccessCode.access_code == access_code.strip().upper(),  # Normalize code
            AccessCode.expires_at > current_time
        ).first()
        
        if not access_code_record:
            # Check if code exists but is expired
            expired_code = db.query(AccessCode).filter(
                AccessCode.user_id == user_id,
                AccessCode.access_code == access_code.strip().upper()
            ).first()
            if expired_code:
                raise ValidationError("Verification code has expired. Please request a new code.")
            else:
                raise ValidationError("Invalid verification code. Please check the code and try again.")
        
        # Update user phone and verification status
        clean_phone = phone.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        user.phone = clean_phone  # Store only digits
        user.is_phone_verified = True
        user.updated_at = datetime.now(timezone.utc)
        
        # Clean up the used access code (same as email verification)
        db.delete(access_code_record)
        db.commit()
        db.refresh(user)
        
        return ResponseFactory.success(
            message="Phone number verified successfully",
            data={
                "phone": user.phone,
                "is_phone_verified": user.is_phone_verified
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to verify phone number: {str(e)}")


def donor_set_password(data: DonorChangePasswordRequest, user_id: int, db: Session):
    """Set initial password for OAuth users"""
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")

        # Check if user already has a password
        if user.has_password():
            raise ValidationError("User already has a password set. Use change password instead.")

        # Set password using the new_password field (ignore current_password for OAuth users)
        user.set_password(data.new_password)
        db.commit()

        return ResponseFactory.success(
            message="Password set successfully"
        )

    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to set password: {str(e)}")


def donor_verify_reset_password_otp(data, db: Session):
    """Verify OTP for password reset and delete the password"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        if data.phone and not user:
            clean_phone = data.phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            user = User.get_by_phone(db, clean_phone)
            if not user:
                user = User.get_by_phone(db, f"+{clean_phone}")
        
        if not user:
            raise ValidationError("User not found")
        
        # Find and validate access code
        current_time = datetime.now(timezone.utc)
        access_code_record = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.otp.strip().upper(),
            AccessCode.expires_at > current_time
        ).first()
        
        if not access_code_record:
            # Check if code exists but is expired
            expired_code = db.query(AccessCode).filter(
                AccessCode.user_id == user.id,
                AccessCode.access_code == data.otp.strip().upper()
            ).first()
            if expired_code:
                raise ValidationError("Verification code has expired. Please request a new code.")
            else:
                raise ValidationError("Invalid verification code. Please check the code and try again.")
        
        # Delete the user's password (set password_hash to None)
        user.password_hash = None
        user.updated_at = datetime.now(timezone.utc)
        
        # Clean up the used access code
        db.delete(access_code_record)
        db.commit()
        db.refresh(user)
        
        return ResponseFactory.success(
            message="Password reset successful. You can now set a new password.",
            data={
                "user_id": user.id,
                "email": user.email,
                "phone": user.phone,
                "has_password": user.has_password()
            }
        )
        
    except MannaException:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to verify reset password OTP: {str(e)}")
