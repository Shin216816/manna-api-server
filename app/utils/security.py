import bcrypt
import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import logging
from app.config import config


class SecurityManager:
    """Enhanced security manager for authentication and authorization"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Validate password strength
        self._validate_password_strength(password)
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if not plain_password or not hashed_password:
            return False
        
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            return False
    
    def _validate_password_strength(self, password: str) -> None:
        """Validate password strength requirements"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with enhanced security"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
        
        # Add standard claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(32),  # Unique token ID
            "iss": config.APP_NAME,  # Issuer
            "aud": "manna-users"  # Audience
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            raise ValueError("Failed to create access token")
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(32),
            "iss": config.APP_NAME,
            "aud": "manna-refresh",
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            raise ValueError("Failed to create refresh token")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token with enhanced error handling"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience=["manna-users", "manna-refresh"],
                issuer=config.APP_NAME
            )
            return dict(payload)
        except JWTError as e:
            return None
        except Exception as e:
            return None
    
    def generate_access_code(self) -> str:
        """Generate secure access code for email verification"""
        # Generate 6-character alphanumeric code (letters and numbers only)
        import string
        alphanumeric_chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphanumeric_chars) for _ in range(6))
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"manna_{secrets.token_urlsafe(32)}"
    
    def sanitize_input(self, input_string: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not input_string:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_string)
        # Remove script tags
        sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE)
        # Remove other potentially dangerous HTML
        sanitized = re.sub(r'<[^>]*>', '', sanitized)
        
        return sanitized.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid US phone number (10 or 11 digits)
        return len(digits_only) in [10, 11]
    
    def rate_limit_key(self, identifier: str, action: str) -> str:
        """Generate rate limiting key"""
        return f"rate_limit:{action}:{identifier}"
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without full verification"""
        try:
            # Decode without verification to get expiration
            payload = jwt.decode(token, key="", options={"verify_signature": False})
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)
            return True
        except Exception:
            return True

# Create global security manager instance
security_manager = SecurityManager(config.SECRET_KEY)

# Backward compatibility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return security_manager.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return security_manager.verify_password(plain_password, hashed_password)

def generate_access_code() -> str:
    """Generate secure access code"""
    return security_manager.generate_access_code()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    return security_manager.create_access_token(data, expires_delta)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    return security_manager.create_refresh_token(data)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    return security_manager.verify_token(token)

def sanitize_input(input_string: str) -> str:
    """Sanitize user input"""
    return security_manager.sanitize_input(input_string)

def validate_email(email: str) -> bool:
    """Validate email format"""
    return security_manager.validate_email(email)

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    return security_manager.validate_phone(phone)

# Security constants
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
ACCESS_CODE_LENGTH = 16
API_KEY_PREFIX = "manna_"

# Security validation functions
def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback"""
    errors = []
    warnings = []
    
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    elif len(password) > PASSWORD_MAX_LENGTH:
        errors.append(f"Password must be no more than {PASSWORD_MAX_LENGTH} characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Additional strength checks
    if len(password) < 12:
        warnings.append("Consider using a longer password for better security")
    
    if re.search(r'(.)\1{2,}', password):
        warnings.append("Avoid repeating characters")
    
    if re.search(r'(123|abc|qwe|password|admin)', password.lower()):
        warnings.append("Avoid common patterns and words")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "strength_score": _calculate_password_strength(password)
    }

def _calculate_password_strength(password: str) -> int:
    """Calculate password strength score (0-100)"""
    score = 0
    
    # Length contribution
    score += min(len(password) * 4, 40)
    
    # Character variety contribution
    if re.search(r'[a-z]', password):
        score += 10
    if re.search(r'[A-Z]', password):
        score += 10
    if re.search(r'\d', password):
        score += 10
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 10
    
    # Bonus for mixed case and numbers
    if re.search(r'[a-z].*[A-Z]|[A-Z].*[a-z]', password):
        score += 5
    if re.search(r'[a-zA-Z].*\d|\d.*[a-zA-Z]', password):
        score += 5
    
    # Penalty for common patterns
    if re.search(r'(.)\1{2,}', password):
        score -= 10
    if re.search(r'(123|abc|qwe|password|admin)', password.lower()):
        score -= 20
    
    return max(0, min(100, score))

def verify_access_code(user_id: int, access_code: str, db) -> bool:
    """Verify access code for password reset"""
    from app.model.m_access_codes import AccessCode
    from datetime import datetime
    
    try:
        # Find the access code for the user
        code_entry = db.query(AccessCode).filter(
            AccessCode.user_id == user_id,
            AccessCode.access_code == access_code
        ).first()
        
        if not code_entry:
            return False
        
        # Check if code has expired
        now = datetime.now(timezone.utc)
        expires_at = code_entry.expires_at
        
        # If expires_at is timezone-naive, assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            # Delete expired code
            db.delete(code_entry)
            db.commit()
            return False
        
        return True
        
    except Exception as e:
        return False
