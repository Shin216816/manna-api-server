import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.schema.auth_schema import AuthRegisterRequest, AuthRegisterResponse, RegisterData, AuthJWTToken, UserData, AuthLoginRequest, AuthLogoutRequest, AuthForgotPasswordRequest, AuthVerifyOtpRequest, AuthResetPasswordRequest, GoogleOAuthRequest, AppleOAuthRequest, RefreshTokenRequest, AuthRegisterConfirmRequest, AuthRegisterCodeResendRequest
from app.model.m_user import User
from app.model.m_access_codes import AccessCode
from app.utils.security import hash_password, verify_password, generate_access_code
from app.utils.jwt_handler import create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS, create_access_token
from app.utils.token_manager import token_manager
from app.utils.send_email import send_email_with_sendgrid
from app.utils.send_sms import send_otp_sms
from app.model.m_refresh_token import RefreshToken
from app.core.messages import get_auth_message
from app.core.responses import ResponseFactory
from app.core.exceptions import (
    ValidationError, UserExistsError, UserNotFoundError, 
    InvalidCredentialsError, AccessCodeError, EmailError, SMSError
)
from app.utils.error_handler import (
    handle_controller_errors, require_email_or_phone, 
    validate_required_fields, validate_user_exists
)
from app.config import config
from fastapi import HTTPException

@handle_controller_errors
def register(data: AuthRegisterRequest, db: Session):
    """User registration for mobile app with enhanced error handling"""
    
    try:
        # Validate required fields
        require_email_or_phone(data.email, data.phone)
        validate_required_fields(
            data.dict(), 
            ['first_name', 'last_name', 'password']
        )

        existing_user = None
        if data.email:
            existing_user = User.get_by_email(db, data.email)
        if data.phone and not existing_user:
            existing_user = User.get_by_phone(db, data.phone)
        
        if existing_user:
            is_email_verified = existing_user.is_email_verified if data.email else False
            is_phone_verified = existing_user.is_phone_verified if data.phone else False
            
            # Check if user is already verified with the provided credentials
            if (data.email and existing_user.email == data.email and is_email_verified) or \
               (data.phone and existing_user.phone == data.phone and is_phone_verified):
                raise UserExistsError(details={
                    "field": "email" if data.email and existing_user.email == data.email and is_email_verified else "phone"
                })
            
            # Update existing unverified user or create new user data
            if existing_user.email == data.email or existing_user.phone == data.phone:
                # Update existing user
                user = existing_user
                user.first_name = data.first_name
                user.last_name = data.last_name
                user.middle_name = data.middle_name
                user.password_hash = hash_password(data.password)
                user.role = "donor"
                
                # Update email/phone if different
                if data.email and data.email != user.email:
                    user.email = data.email
                    user.is_email_verified = False
                if data.phone and data.phone != user.phone:
                    user.phone = data.phone
                    user.is_phone_verified = False
                    
                db.commit()
                db.refresh(user)
            else:
                # Create new user with different credentials
                user = User(
                    first_name=data.first_name,
                    last_name=data.last_name,
                    middle_name=data.middle_name,
                    email=data.email,
                    phone=data.phone,
                    password_hash=hash_password(data.password),
                    role="donor",
                    is_email_verified=False,
                    is_phone_verified=False,
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        else:
            user = User(
                first_name=data.first_name,
                last_name=data.last_name,
                middle_name=data.middle_name,
                email=data.email,
                phone=data.phone,
                password_hash=hash_password(data.password),
                role="donor",  # Explicitly set role to "donor" for mobile app users
                is_email_verified=False,
                is_phone_verified=False,
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
        
        
        # Check if AccessCode table exists
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()
            
            
            if 'access_codes' in tables:
                pass
            else:
                raise Exception("AccessCode table not found in database")
        except Exception as table_error:
            raise Exception(f"Database table error: {table_error}")
        # Generate access code for verification
        access_code = generate_access_code()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=120)
        
        # Create access code record
        code_record = AccessCode(
            user_id=user.id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()
        
        # Verify the commit worked by checking the database
        db.refresh(code_record)
        
        # Send verification code via email or SMS
        if data.email:
            send_email_with_sendgrid(
                to_email=data.email,
                subject="Verify your Manna account",
                body_html=f"Your verification code is: {access_code}"
            )
        if data.phone:
            send_otp_sms(data.phone, access_code)

        return ResponseFactory.success(
            message="Registration successful. Please verify your account.",
            data={
                "user_id": user.id,
                "access_code": access_code,
                "expires_at": expires_at.isoformat(),
                "message": "Please check your email/phone for verification code"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to register user")

def register_code_resend(data: AuthRegisterCodeResendRequest, db: Session):
    """Resend registration access code"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user.id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()

        access_code = generate_access_code()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=120)

        code_record = AccessCode(
            user_id=user.id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()

        if data.email:
            send_email_with_sendgrid(
                to_email=data.email,
                subject="Verify your Manna account",
                body_html=f"Your verification code is: {access_code}"
            )
        if data.phone:
            send_otp_sms(data.phone, access_code)

        return ResponseFactory.success(
            message="Verification code sent successfully",
            data={
                "access_code": access_code,
                "expires_at": expires_at.isoformat(),
                "message": "Access code sent successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to resend code")

def login(data: AuthLoginRequest, db: Session, request=None):
    """Standard login for mobile app"""
    try:
        user = None

        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)

        if not user:
            raise HTTPException(
                status_code=401, 
                detail=ResponseFactory.auth_error(
                    message="Login failed - User not found",
                    error_code="USER_NOT_FOUND",
                    details={
                        "email": data.email,
                        "phone": data.phone,
                        "suggestion": "Please check your credentials or register a new account"
                    }
                ).dict()
            )

        if not user.has_password():
            if user.is_phone_verified and user.phone:
                # Handle phone-verified users properly
                # Allow login via phone verification or prompt for password setup
                return handle_phone_verified_login(user, db, request)
            else:
                raise HTTPException(
                    status_code=401, 
                    detail=ResponseFactory.auth_error(
                        message="Password not set for this account",
                        error_code="PASSWORD_NOT_SET",
                        details={
                            "account_type": "OAuth" if user.google_id or user.apple_id else "Phone-only",
                            "suggestion": "Please use the same sign-in method you used to create this account, or set up a password in your account settings"
                        }
                    ).dict()
                )

        if user.has_password():
            if not user.verify_password(data.password):
                raise HTTPException(
                    status_code=401, 
                    detail=ResponseFactory.auth_error(
                        message="Login failed - Invalid password",
                        error_code="INVALID_PASSWORD",
                        details={
                            "suggestion": "Please check your password and try again",
                            "remaining_attempts": "unlimited"  # You could implement rate limiting here
                        }
                    ).dict()
                )

        if not user.is_active:
            raise HTTPException(
                status_code=401, 
                detail=ResponseFactory.auth_error(
                    message="Account is disabled",
                    error_code="ACCOUNT_DISABLED",
                    details={
                        "suggestion": "Please contact support to reactivate your account",
                        "reason": "Account has been deactivated"
                    }
                ).dict()
            )

        if not user.is_email_verified and not user.google_id and not user.apple_id:
            raise HTTPException(
                status_code=401, 
                detail=ResponseFactory.auth_error(
                    message="Email not verified",
                    error_code="EMAIL_NOT_VERIFIED",
                    details={
                        "suggestion": "Please verify your email address before logging in",
                        "verification_method": "email",
                        "can_resend": True
                    }
                ).dict()
            )

        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        access_token, jti, session_id = token_manager.create_access_token({
            "user_id": user.id,  # Add user_id for session management
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }, request=request)

        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)

        return ResponseFactory.success(
            message=get_auth_message("LOGIN_SUCCESS"),
            data={
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token_obj.token,
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "middle_name": user.middle_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                    "is_active": user.is_active,
                    "churches": [
                        {
                            "id": membership.church.id,
                            "name": membership.church.name,
                            "role": membership.role,
                            "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                        }
                        for membership in user.get_all_churches(db)
                    ],
                    "stripe_customer_id": user.stripe_customer_id,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=get_auth_message("LOGIN_ERROR"))

def logout(data: AuthLogoutRequest, db: Session):
    """Logout user"""
    try:
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == data.refresh_token
        ).first()
        
        if token_record:
            db.delete(token_record)
            db.commit()

        return ResponseFactory.success(message=get_auth_message("LOGOUT_SUCCESS"))

    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail=get_auth_message("LOGOUT_ERROR"))

def forgot_password(data: AuthForgotPasswordRequest, db: Session):
    """Send password reset instructions to user"""
    try:
        email = data.email if data.email else None
        phone = data.phone if data.phone else None
        
        if not email and not phone:
            raise HTTPException(
                status_code=400, 
                detail=ResponseFactory.validation_error(
                    details={
                        "error": "Either email or phone is required",
                        "suggestion": "Please provide either an email address or phone number to reset your password"
                    }
                ).dict()
            )
        
        user = None
        if email:
            user = User.get_by_email(db, email)
        if phone and not user:
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            user = User.get_by_phone(db, clean_phone)
            if not user:
                user = User.get_by_phone(db, f"+{clean_phone}")
        
        if not user:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.user_error(
                    message="User not found",
                    error_code="USER_NOT_FOUND",
                    details={
                        "email": email,
                        "phone": phone,
                        "suggestion": "No account found with the provided information. Please check your details or register a new account."
                    }
                ).dict()
            )

        existing_codes = db.query(AccessCode).filter(AccessCode.user_id == user.id).all()
        for code in existing_codes:
            db.delete(code)
        db.commit()

        access_code = generate_access_code()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=300)

        code_record = AccessCode(
            user_id=user.id,
            access_code=access_code,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc)
        )

        db.add(code_record)
        db.commit()

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

    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Failed to send password reset")

def verify_otp(data: AuthVerifyOtpRequest, db: Session):
    """Verify OTP for password reset"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.access_code,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not access_code:
            raise HTTPException(status_code=400, detail="Invalid or expired code")

        return ResponseFactory.success(
            message="OTP verified successfully",
            data={"user_id": user.id}
        )

    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

def reset_password(data: AuthResetPasswordRequest, db: Session):
    """Reset password with OTP"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.access_code,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()

        if not access_code:
            raise HTTPException(status_code=400, detail="Invalid or expired code")

        user.password_hash = hash_password(data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        db.delete(access_code)
        db.commit()

        return ResponseFactory.success(
            message="Password reset successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Failed to reset password")

def google_oauth_login(data: GoogleOAuthRequest, db: Session):
    """Google OAuth login for mobile app"""
    try:
        # Use the existing Google OAuth implementation
        from app.controller.auth.google_oauth import google_oauth_login as original_google_oauth
        return original_google_oauth(data, db)
    except ImportError:
        # Fallback implementation if import fails
        raise HTTPException(status_code=500, detail="Google OAuth service unavailable")

    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail=get_auth_message("TOKEN_REFRESH_ERROR"))

def biometric_login(biometric_token: str, db: Session, request=None):
    """Biometric login for mobile app"""
    try:
        # In a production environment, this would verify the biometric token
        # For now, we'll implement a basic token-based authentication
        # that could be extended with proper biometric verification
        
        # Decode the biometric token (this would be a JWT or similar)
        # For production, this should be properly verified with biometric data
        from jose import jwt, JWTError
        from app.config import config
        
        try:
            # Verify the biometric token
            payload = jwt.decode(
                biometric_token,
                config.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid biometric token")
            
            # Get user
            user = User.get_by_id(db, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if not user.is_active:
                raise HTTPException(status_code=401, detail="Account is inactive")
            
            # Generate new tokens
            access_token, jti, session_id = token_manager.create_access_token({
                "user_id": user.id,  # Add user_id for session management
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }, request=request)
            
            refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)
            
            return ResponseFactory.success(
                message="Biometric login successful",
                data={
                    "tokens": {
                        "access_token": access_token,
                        "refresh_token": refresh_token_obj.token,
                        "token_type": "bearer",
                        "expires_in": 3600
                    },
                    "user": {
                        "id": user.id,
                        "first_name": user.first_name,
                        "middle_name": user.middle_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone": user.phone,
                        "is_email_verified": user.is_email_verified,
                        "is_phone_verified": user.is_phone_verified,
                        "is_active": user.is_active,
                        "churches": [
                            {
                                "id": membership.church.id,
                                "name": membership.church.name,
                                "role": membership.role,
                                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                            }
                            for membership in user.get_all_churches(db)
                        ],
                        "stripe_customer_id": user.stripe_customer_id,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None
                    }
                }
            )
            
        except jwt.JWSError:
            raise HTTPException(status_code=401, detail="Invalid biometric token")
            
    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Biometric login failed")

def handle_phone_verified_login(user, db: Session, request=None):
    """Handle login for phone-verified users without passwords"""
    try:
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Generate tokens
        access_token, jti, session_id = token_manager.create_access_token({
            "user_id": user.id,  # Add user_id for session management
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }, request=request)

        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)

        return ResponseFactory.success(
            message="Phone-verified login successful",
            data={
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token_obj.token,
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "middle_name": user.middle_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                    "is_active": user.is_active,
                    "churches": [
                        {
                            "id": membership.church.id,
                            "name": membership.church.name,
                            "role": membership.role,
                            "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                        }
                        for membership in user.get_all_churches(db)
                    ],
                    "stripe_customer_id": user.stripe_customer_id,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
            }
        )
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Phone-verified login failed")


def change_mobile_password(user_id: int, old_password: str, new_password: str, db: Session):
    """Change user password for mobile app"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.user_error(
                    message="User not found",
                    error_code="USER_NOT_FOUND",
                    details={
                        "user_id": user_id,
                        "suggestion": "Please check the user ID and try again"
                    }
                ).dict()
            )
        
        if not user.password_hash:
            raise HTTPException(
                status_code=400, 
                detail=ResponseFactory.auth_error(
                    message="No password set for this account",
                    error_code="NO_PASSWORD_SET",
                    details={
                        "suggestion": "This account was created without a password. Please use the original sign-in method."
                    }
                ).dict()
            )
        
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=400, 
                detail=ResponseFactory.auth_error(
                    message="Invalid current password",
                    error_code="INVALID_CURRENT_PASSWORD",
                    details={
                        "suggestion": "Please check your current password and try again"
                    }
                ).dict()
            )
        
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return ResponseFactory.success(
            message="Password changed successfully",
            data={"user_id": user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(
            status_code=500, 
            detail=ResponseFactory.server_error(
                message="Failed to change password",
                request_id=None
            ).dict()
        )


def add_user_to_church(user_id: int, church_id: int, db: Session, role: str = "member"):
    """Add user to a church with specified role"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.user_error(
                    message="User not found",
                    error_code="USER_NOT_FOUND",
                    details={
                        "user_id": user_id,
                        "suggestion": "Please check the user ID and try again"
                    }
                ).dict()
            )
        
        # Check if church exists
        from app.model.m_church import Church
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.church_error(
                    message="Church not found",
                    error_code="CHURCH_NOT_FOUND",
                    details={
                        "church_id": church_id,
                        "suggestion": "Please check the church ID and try again"
                    }
                ).dict()
            )
        
        # Add user to church
        success = user.add_church_membership(db, church_id, role)
        
        if success:
            return ResponseFactory.success(
                message="User added to church successfully",
                data={
                    "user_id": user_id,
                    "church_id": church_id,
                    "role": role,
                    "church_name": church.name
                }
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=ResponseFactory.church_error(
                    message="Failed to add user to church",
                    error_code="CHURCH_ADD_FAILED",
                    details={
                        "user_id": user_id,
                        "church_id": church_id,
                        "suggestion": "Please try again or contact support if the issue persists"
                    }
                ).dict()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Failed to add user to church")


def remove_user_from_church(user_id: int, church_id: int, db: Session):
    """Remove user from a church"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.user_error(
                    message="User not found",
                    error_code="USER_NOT_FOUND",
                    details={
                        "user_id": user_id,
                        "suggestion": "Please check the user ID and try again"
                    }
                ).dict()
            )
        
        # Check if church exists
        from app.model.m_church import Church
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.church_error(
                    message="Church not found",
                    error_code="CHURCH_NOT_FOUND",
                    details={
                        "church_id": church_id,
                        "suggestion": "Please check the church ID and try again"
                    }
                ).dict()
            )
        
        # Remove user from church
        success = user.remove_church_membership(db, church_id)
        
        if success:
            return ResponseFactory.success(
                message="User removed from church successfully",
                data={
                    "user_id": user_id,
                    "church_id": church_id,
                    "church_name": church.name
                }
            )
        else:
            raise HTTPException(
                status_code=404, 
                detail=ResponseFactory.church_error(
                    message="User is not a member of this church",
                    error_code="USER_NOT_MEMBER",
                    details={
                        "user_id": user_id,
                        "church_id": church_id,
                        "church_name": church.name,
                        "suggestion": "The user is not currently a member of this church"
                    }
                ).dict()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Failed to remove user from church")


def get_user_churches(user_id: int, db: Session):
    """Get all churches for a user"""
    try:
        user = User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        churches = user.get_all_churches(db)
        
        church_data = [
            {
                "id": membership.church.id,
                "name": membership.church.name,
                "role": membership.role,
                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
                "is_active": membership.is_active
            }
            for membership in churches
        ]
        
        return ResponseFactory.success(
            message="User churches retrieved successfully",
            data={"churches": church_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        pass
        raise HTTPException(status_code=500, detail="Failed to get user churches")

@handle_controller_errors
def refresh_token(data: RefreshTokenRequest, db: Session):
    """Refresh access token using refresh token"""
    try:
        # Find the refresh token in database
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == data.refresh_token
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=401,
                detail=ResponseFactory.auth_error(
                    message="Invalid refresh token",
                    error_code="INVALID_REFRESH_TOKEN",
                    details={
                        "suggestion": "Please login again to get a new token"
                    }
                ).dict()
            )
        
        # Check if token is expired
        if token_record.is_expired():
            # Clean up expired token
            db.delete(token_record)
            db.commit()
            raise HTTPException(
                status_code=401,
                detail=ResponseFactory.auth_error(
                    message="Refresh token expired",
                    error_code="REFRESH_TOKEN_EXPIRED",
                    details={
                        "suggestion": "Please login again to get a new token"
                    }
                ).dict()
            )
        
        # Get user
        user = User.get_by_id(db, token_record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail=ResponseFactory.auth_error(
                    message="User not found or inactive",
                    error_code="USER_INACTIVE",
                    details={
                        "suggestion": "Please contact support if your account was deactivated"
                    }
                ).dict()
            )
        
        # Create new access token
        access_token, jti, session_id = token_manager.create_access_token({
            "user_id": user.id,
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        
        # Update token last used time
        token_record.last_used_at = datetime.now(timezone.utc)
        db.commit()
        
        return ResponseFactory.success(
            message="Token refreshed successfully",
            data={
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": token_record.token,  # Keep same refresh token
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to refresh token")

@handle_controller_errors
def register_code_confirm(data: AuthRegisterConfirmRequest, db: Session):
    """Confirm registration with access code"""
    try:
        # Find user by email or phone
        user = None
        if data.email:
            user = User.get_by_email(db, data.email)
        elif data.phone:
            user = User.get_by_phone(db, data.phone)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=ResponseFactory.user_error(
                    message="User not found",
                    error_code="USER_NOT_FOUND",
                    details={
                        "email": data.email,
                        "phone": data.phone,
                        "suggestion": "Please check your credentials or register first"
                    }
                ).dict()
            )
        
        # Find and validate access code
        access_code = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data.access_code,
            AccessCode.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not access_code:
            raise HTTPException(
                status_code=400,
                detail=ResponseFactory.auth_error(
                    message="Invalid or expired verification code",
                    error_code="INVALID_ACCESS_CODE",
                    details={
                        "suggestion": "Please check the code or request a new one"
                    }
                ).dict()
            )
        
        # Mark user as verified
        if data.email and user.email == data.email:
            user.is_email_verified = True
        if data.phone and user.phone == data.phone:
            user.is_phone_verified = True
        
        user.updated_at = datetime.now(timezone.utc)
        
        # Clean up the used access code
        db.delete(access_code)
        db.commit()
        db.refresh(user)
        
        # Generate tokens for the verified user
        access_token, jti, session_id = token_manager.create_access_token({
            "user_id": user.id,
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        
        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)
        
        return ResponseFactory.success(
            message="Registration confirmed successfully",
            data={
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token_obj.token,
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "middle_name": user.middle_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to confirm registration")

def apple_oauth_login(data: AppleOAuthRequest, db: Session):
    """Apple OAuth login for mobile app"""
    try:
        # Use the existing Apple OAuth implementation if available
        from app.controller.auth.apple_oauth import apple_oauth_login as original_apple_oauth
        return original_apple_oauth(data, db)
    except ImportError:
        # Fallback implementation if import fails
        raise HTTPException(status_code=501, detail="Apple OAuth service not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Apple OAuth login failed")
