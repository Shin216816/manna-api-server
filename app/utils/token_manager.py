"""
Enhanced Token Management System for Manna Backend

This module provides comprehensive token management including:
- JWT access and refresh token creation/validation
- Token blacklisting and rotation
- Session management
- Security features like JTI tracking
"""

from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
# BlacklistedToken model removed - using RefreshToken management
from app.model.m_refresh_token import RefreshToken
from app.services.session_service import session_manager
from app.utils.database import SessionLocal
from app.config import config
import secrets
import hashlib
import logging
import json

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = config.REFRESH_TOKEN_EXPIRE_DAYS


class TokenManager:
    """Enhanced token management with security features"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None, 
                           request: Optional[Any] = None) -> Tuple[str, str, Optional[str]]:
        """
        Create JWT access token with JTI for blacklisting and session management
        Returns: (token, jti, session_id)
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        # Generate unique JTI for this token
        jti = secrets.token_urlsafe(32)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": jti,
            "iss": config.APP_NAME,
            "aud": "manna-users",
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # Create session if request context is available and user_id exists
            session_id = None
            if request and "user_id" in data and data["user_id"]:
                try:
                    device_info = self.extract_device_info(request)
                    ip_address = getattr(request, 'client', [None])[0] if hasattr(request, 'client') else None
                    user_agent = request.headers.get("user-agent", "")
                    
                    session_id = session_manager.create_session(
                        user_id=data["user_id"],
                        user_type=data.get("role", "user"),
                        church_id=data.get("church_id"),
                        device_info=device_info,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        access_token_jti=jti
                    )
                except Exception as session_error:
                    pass
            else:
                if "user_id" not in data:
                    pass
                elif not data.get("user_id"):
                    pass
                else:
                    pass
            
            return encoded_jwt, jti, session_id
        except Exception as e:
            raise ValueError("Failed to create access token")

    def create_refresh_token_record(self, user_id: int, db, device_info: Optional[dict] = None, 
                                  ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> RefreshToken:
        """Create refresh token database record"""
        return RefreshToken.create_token(
            user_id=user_id,
            db=db,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def verify_access_token(self, token: str, db) -> Optional[Dict[str, Any]]:
        """Verify access token and check blacklist and session validity"""
        try:
            # First try to decode with strict validation (new tokens)
            try:
                payload = jwt.decode(
                    token, 
                    self.secret_key, 
                    algorithms=[self.algorithm],
                    audience="manna-users",
                    issuer=config.APP_NAME
                )
            except JWTError as jwt_error:
                # Check if it's an expiration error specifically
                if "expired" in str(jwt_error).lower() or "exp" in str(jwt_error).lower():
                    # Return a special payload indicating expiration
                    return {"expired": True, "error": "token_expired"}
                
                # If that fails, try without audience/issuer validation (old tokens)
                try:
                    payload = jwt.decode(
                        token, 
                        self.secret_key, 
                        algorithms=[self.algorithm],
                        options={"verify_aud": False, "verify_iss": False}
                    )
                except JWTError as legacy_error:
                    if "expired" in str(legacy_error).lower() or "exp" in str(legacy_error).lower():
                        return {"expired": True, "error": "token_expired"}
                    else:
                        return None
            
            # Check if JTI is blacklisted (using RefreshToken management)
            jti = payload.get("jti")
            if jti:
                # Check if any refresh token with this JTI is inactive
                invalid_token = db.query(RefreshToken).filter(
                    RefreshToken.token == jti,
                    RefreshToken.is_active == False
                ).first()
                if invalid_token:
                    return None
            
            # Check if session is still valid (only for tokens that have JTI)
            if jti:
                session = session_manager.find_session_by_token_jti(jti)
                if session:
                    # Update session activity
                    session_manager.update_session_activity(session.session_id)
                    
                    # Convert payload to dict and add session info
                    payload_dict = dict(payload)
                    payload_dict["session_id"] = session.session_id
                    payload_dict["user_type"] = session.user_type
                    payload_dict["church_id"] = session.church_id
                    
                    return payload_dict
                else:
                    # Token has JTI but no session - this could be a legacy token
                    # or a token created without request context
                    # Return payload without session info for backward compatibility
                    return dict(payload)
            
            # For tokens without JTI (legacy tokens), return payload as-is
            return dict(payload)
            
        except JWTError as e:
            return None
        except Exception as e:
            return None

    def verify_refresh_token(self, token: str, db) -> Optional[RefreshToken]:
        """Verify refresh token from database"""
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if token_record:
            # Update last used timestamp
            token_record.last_used = datetime.now(timezone.utc)
            db.commit()
            
        return token_record

    def rotate_refresh_token(self, old_token: str, db, device_info: Optional[dict] = None,
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[RefreshToken]:
        """Rotate refresh token for security"""
        return RefreshToken.rotate_token(
            old_token=old_token,
            db=db,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def blacklist_access_token(self, token: str, db, user_id: Optional[int] = None, reason: str = "logout"):
        """Blacklist access token by its JTI using RefreshToken management"""
        try:
            # Decode token to get JTI and expiration
            payload = jwt.decode(token, key="", options={"verify_signature": False})
            jti = payload.get("jti")
            
            if jti:
                # Create an inactive refresh token to mark this JTI as blacklisted
                blacklisted_token = RefreshToken(
                    user_id=user_id or 0,
                    token=jti,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),  # Short expiration
                    is_active=False
                )
                db.add(blacklisted_token)
                db.commit()
                return True
            return False
        except Exception as e:
            return False

    def logout_user(self, access_token: str, refresh_token: str, db, user_id: int):
        """Complete logout - blacklist access token and remove refresh token"""
        try:
            # Blacklist the access token
            self.blacklist_access_token(access_token, db, user_id, "logout")
            
            # Remove refresh token
            token_record = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id
            ).first()
            
            if token_record:
                db.delete(token_record)
                db.commit()
                
            return True
        except Exception as e:
            return False

    def force_logout_user(self, user_id: int, db, reason: str = "forced_logout"):
        """Force logout user from all sessions"""
        try:
            # Deactivate all user refresh tokens
            user_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_active == True
            ).all()
            
            for token in user_tokens:
                token.is_active = False
                
            db.commit()
            return True
        except Exception as e:
            return False

    def get_user_sessions(self, user_id: int, db):
        """Get all active sessions for user"""
        return RefreshToken.get_user_sessions(user_id, db)

    def revoke_session(self, session_id: int, db, user_id: int):
        """Revoke specific session"""
        token_record = db.query(RefreshToken).filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == user_id,
            RefreshToken.is_active == True
        ).first()
        
        if token_record:
            token_record.is_active = False
            # Mark the refresh token as inactive
            token_record.is_active = False
            db.commit()
            return True
        return False

    def cleanup_expired_tokens(self):
        """Clean up expired tokens from database"""
        db = SessionLocal()
        try:
            # Clean refresh tokens
            refresh_cleaned = RefreshToken.cleanup_expired(db)
            
            # Clean expired tokens (blacklisted tokens are now handled by RefreshToken)
            return refresh_cleaned
        finally:
            db.close()

    def extract_device_info(self, request) -> dict:
        """Extract device information from request headers"""
        user_agent = request.headers.get("user-agent", "")
        
        # Basic device detection
        device_type = "unknown"
        if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
            device_type = "mobile"
        elif "Tablet" in user_agent or "iPad" in user_agent:
            device_type = "tablet"
        else:
            device_type = "desktop"
            
        browser = "unknown"
        if "Chrome" in user_agent:
            browser = "chrome"
        elif "Firefox" in user_agent:
            browser = "firefox"
        elif "Safari" in user_agent:
            browser = "safari"
        elif "Edge" in user_agent:
            browser = "edge"
            
        return {
            "device_type": device_type,
            "browser": browser,
            "user_agent": user_agent[:200]  # Limit length
        }


# Global token manager instance
token_manager = TokenManager()

# Legacy function compatibility
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Legacy function - returns only token"""
    token, jti, session_id = token_manager.create_access_token(data, expires_delta)
    return token

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Legacy function - verify access token"""
    db = SessionLocal()
    try:
        return token_manager.verify_access_token(token, db)
    finally:
        db.close()

def create_refresh_token(data: Optional[Dict[str, Any]] = None) -> str:
    """Legacy function - creates simple refresh token"""
    if data is None:
        data = {}
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Legacy function - verify refresh token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return dict(payload)
    except JWTError:
        return None

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Legacy function - use verify_access_token instead"""
    return verify_access_token(token)
