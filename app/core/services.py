"""
Unified service layer for business logic operations.
Eliminates code duplication and provides reusable business logic functions.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging

from app.core.constants import (
    AUTH_CONSTANTS, BUSINESS_CONSTANTS, ERROR_MESSAGES, get_auth_constant
)
from app.core.exceptions import (
    UserNotFoundError, UserExistsError, InvalidCredentialsError,
    AccessCodeError, DatabaseError, EmailError, AuthorizationError
)
from app.core.messages import (
    get_auth_message,
    get_bank_message,
    get_church_message,
    get_admin_message
)
from app.core.responses import ResponseFactory
from app.model.m_user import User
from app.model.m_access_codes import AccessCode
from app.model.m_refresh_token import RefreshToken
from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.utils.security import hash_password, verify_password, generate_access_code
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.utils.send_email import send_email_with_sendgrid


class AuthService:
    """Authentication service for user registration, login, and token management"""
    
    @staticmethod
    def register_user(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Register a new user with email verification
        
        Args:
            data: User registration data
            db: Database session
            
        Returns:
            Dict containing registration result and access code
        """
        email = data.get("email")
        if not email:
            raise AccessCodeError(ERROR_MESSAGES["EMAIL_OR_PHONE_REQUIRED"])
        
        # Check if user already exists
        existing_user = User.get_by_email(db, email)
        if existing_user:
            raise UserExistsError()
        
        try:
            # Create new user
            new_user = User(
                first_name=data["first_name"],
                last_name=data.get("last_name"),
                middle_name=data.get("middle_name"),
                email=email,
                phone=BUSINESS_CONSTANTS["DEFAULT_PHONE"],
                password=hash_password(data["password"]),
                church_id=BUSINESS_CONSTANTS["DEFAULT_CHURCH_ID"]
            )
            db.add(new_user)
            db.flush()
            
            # Generate and store access code
            code = generate_access_code()
            access_code = AccessCode(
                user_id=new_user.id,
                access_code=code,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=AUTH_CONSTANTS["ACCESS_CODE_EXPIRE_SECONDS"]),
                created_at=datetime.now(timezone.utc)
            )
            db.add(access_code)
            db.commit()
            
            db.refresh(new_user)
            db.refresh(access_code)
            
            # Send verification email
            try:
                send_email_with_sendgrid(to_email=email, code=code)
            except Exception as e:
                error(f"Failed to send email: {e}")
                # Don't fail registration if email fails
            
            return {
                "success": True,
                "message": get_auth_message("USER_REGISTER_SUCCESS"),
                "access_code": code,
            }
            
        except Exception as e:
            db.rollback()
            error(f"Registration failed: {e}")
            raise DatabaseError("User registration failed")
    
    @staticmethod
    def confirm_registration(data: Dict[str, Any], db: Session) -> Any:
        """
        Confirm user registration with access code
        
        Args:
            data: Confirmation data with email and access code
            db: Database session
            
        Returns:
            Dict containing authentication tokens
        """
        email = data.get("email")
        if not email:
            raise AccessCodeError(ERROR_MESSAGES["EMAIL_OR_PHONE_REQUIRED"])
        
        # Find user
        user = User.get_by_email(db, email)
        if not user:
            raise UserNotFoundError()
        
        # Verify access code
        code_entry = db.query(AccessCode).filter(
            AccessCode.user_id == user.id,
            AccessCode.access_code == data["access_code"]
        ).first()
        
        if not code_entry:
            raise AccessCodeError(ERROR_MESSAGES["ACCESS_CODE_INVALID"])
        
        if code_entry.expires_at < datetime.now(timezone.utc):
            db.delete(code_entry)
            db.commit()
            raise AccessCodeError(ERROR_MESSAGES["ACCESS_CODE_EXPIRED"])
        
        # Mark email as verified and clean up
        user.is_email_verified = True
        db.delete(code_entry)
        db.commit()
        
        # Generate tokens
        access_token = create_access_token({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        
        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)
        
        return ResponseFactory.auth_success(
            access_token=access_token,
            refresh_token=str(refresh_token_obj.token),
            expires_in=(get_auth_constant("TOKEN_EXPIRE_MINUTES") or 30) * 60
        )
    
    @staticmethod
    def login_user(data: Dict[str, Any], db: Session) -> Any:
        """
        Authenticate user and generate tokens
        
        Args:
            data: Login credentials
            db: Database session
            
        Returns:
            Dict containing authentication tokens
        """
        email = data.get("email")
        if not email:
            raise InvalidCredentialsError()
        
        # Find and verify user
        user = User.get_by_email(db, email)
        if not user or not verify_password(data["password"], user.password):
            raise InvalidCredentialsError()
        
        # Generate tokens
        access_token = create_access_token({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        
        refresh_token_obj = RefreshToken.create_token(user.id, db, create_refresh_token)
        
        return  ResponseFactory.auth_success(
            access_token=access_token,
            refresh_token=str(refresh_token_obj.token),
            expires_in=(get_auth_constant("TOKEN_EXPIRE_MINUTES") or 30) * 60
        )
    
    @staticmethod
    def resend_access_code(data: Dict[str, Any], db: Session) -> Any:
        """
        Resend access code for email verification
        
        Args:
            data: Resend request data
            db: Database session
            
        Returns:
            Dict containing resend result
        """
        email = data.get("email")
        if not email:
            raise AccessCodeError(ERROR_MESSAGES["EMAIL_OR_PHONE_REQUIRED"])
        
        # Find user
        user = User.get_by_email(db, email)
        if not user:
            raise UserNotFoundError()
        
        now = datetime.now(timezone.utc)
        
        try:
            # Check for existing code and throttle
            existing_code = db.query(AccessCode).filter(
                AccessCode.user_id == user.id
            ).order_by(AccessCode.created_at.desc()).first()
            
            if existing_code and (now - existing_code.created_at) < timedelta(seconds=  get_auth_constant("ACCESS_CODE_RESEND_COOLDOWN_SECONDS") or 60):
                raise AccessCodeError(ERROR_MESSAGES["ACCESS_CODE_TOO_SOON"])
            
            if existing_code:
                # Update existing code
                existing_code.access_code = generate_access_code()
                existing_code.expires_at = now + timedelta(seconds=get_auth_constant("ACCESS_CODE_EXPIRE_SECONDS") or 60)
                existing_code.created_at = now
                db.commit()
                db.refresh(existing_code)
                code = existing_code.access_code
            else:
                # Create new code
                new_code = AccessCode(
                    user_id=user.id,
                    access_code=generate_access_code(),
                    expires_at=now + timedelta(seconds=AUTH_CONSTANTS["ACCESS_CODE_EXPIRE_SECONDS"]),
                    created_at=now
                )
                db.add(new_code)
                db.commit()
                db.refresh(new_code)
                code = new_code.access_code
            
            # Send email
            try:
                send_email_with_sendgrid(to_email=email, code=str(code))
            except Exception as e:
                error(f"Failed to send email: {e}")
                raise EmailError("Failed to send access code")
            
            return ResponseFactory.success(get_auth_message("ACCESS_CODE_SENT"))
            
        except Exception as e:
            db.rollback()
            error(f"Resend failed: {e}")
            raise DatabaseError("Failed to resend access code")


class UserService:
    """User management service"""
    
    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(email: str, db: Session) -> Optional[User]:
        """Get user by email"""
        return User.get_by_email(db, email)
    
    @staticmethod
    def update_user_profile(user_id: int, data: Dict[str, Any], db: Session) -> User:
        """Update user profile"""
        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise UserNotFoundError()
        
        for field, value in data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str, db: Session) -> bool:
        """Change user password"""
        user = UserService.get_user_by_id(user_id, db)
        if not user:
            raise UserNotFoundError()
        
        if not verify_password(old_password, str(user.password)):
            raise InvalidCredentialsError(details={"message": "Invalid old password"})
        
        setattr(user, 'password', hash_password(new_password))
        db.commit()
        return True


class ChurchService:
    """Church management service"""
    
    @staticmethod
    def get_church_by_id(church_id: int, db: Session) -> Optional[Church]:
        """Get church by ID"""
        return db.query(Church).filter(Church.id == church_id).first()
    
    @staticmethod
    def get_active_churches(db: Session) -> List[Church]:
        """Get all active churches"""
        return db.query(Church).filter(Church.is_active == True).all()
    
    @staticmethod
    def create_church(data: Dict[str, Any], db: Session) -> Church:
        """Create a new church"""
        church = Church(**data)
        db.add(church)
        db.commit()
        db.refresh(church)
        return church
    
    @staticmethod
    def update_church(church_id: int, data: Dict[str, Any], db: Session) -> Church:
        """Update church information"""
        church = ChurchService.get_church_by_id(church_id, db)
        if not church:
            raise UserNotFoundError(details={"message": "Church not found"})
        
        for field, value in data.items():
            if hasattr(church, field) and value is not None:
                setattr(church, field, value)
        
        db.commit()
        db.refresh(church)
        return church


class AdminService:
    """Admin management service"""
    
    @staticmethod
    def authenticate_church_admin(admin_id: int, db: Session) -> Dict[str, Any]:
        """Authenticate church admin"""
        admin = db.query(ChurchAdmin).filter(ChurchAdmin.id == admin_id).first()
        if not admin:
            raise UserNotFoundError(details={"message": "Admin not found"})
        
        # Get the user associated with this admin to access email
        from app.model.m_user import User
        user = db.query(User).filter(User.id == admin.user_id).first()
        if not user:
            raise UserNotFoundError(details={"message": "User not found"})
        
        church = ChurchService.get_church_by_id(admin.church_id, db)
        if not church or not church.is_active:
            raise AccessCodeError(ERROR_MESSAGES["CHURCH_DISABLED"])
        
        return {
            "admin_id": admin.id,
            "user_id": admin.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "church_id": admin.church_id,
            "role": "church_admin"
        }
    
    @staticmethod
    def authenticate_platform_admin(admin_id: int, db: Session) -> Dict[str, Any]:
        """Authenticate platform admin"""
        admin = db.query(ChurchAdmin).filter(ChurchAdmin.id == admin_id).first()
        if not admin or admin.role != "platform_admin":
            raise AuthorizationError()
        
        return {
            "admin_id": admin.id,
            "role": "platform_admin"
        }


# Service factory for easy access
class ServiceFactory:
    """Factory class for accessing services"""
    
    @staticmethod
    def auth() -> AuthService:
        return AuthService()
    
    @staticmethod
    def user() -> UserService:
        return UserService()
    
    @staticmethod
    def church() -> ChurchService:
        return ChurchService()
    
    @staticmethod
    def admin() -> AdminService:
        return AdminService() 
