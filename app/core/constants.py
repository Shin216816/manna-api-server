"""
Centralized constants for the Manna application.
All configuration constants should be defined here to avoid duplication.
"""

# ============================
# Authentication Constants
# ============================
AUTH_CONSTANTS = {
    "TOKEN_EXPIRE_MINUTES": 30,
    "EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES": 15,
    "REFRESH_TOKEN_EXPIRE_DAYS": 30,
    "ACCESS_CODE_EXPIRE_SECONDS": 60,
    "ACCESS_CODE_RESEND_COOLDOWN_SECONDS": 60,
    "PASSWORD_MIN_LENGTH": 8,
    "JWT_ALGORITHM": "HS256",
    "JWT_EXPIRES_IN_SECONDS": 1800,
    "JWT_TOKEN_TYPE": "bearer",
    "JWT_AUDIENCE": ["manna-users", "manna-refresh"],
}

# ============================
# Business Logic Constants
# ============================
BUSINESS_CONSTANTS = {
    "REFERRAL_COMMISSION_RATE": 0.10,
    "DEFAULT_DONATION_MULTIPLIER": 1.0,
    "MAX_DONATION_AMOUNT": 1000.0,
    "DEFAULT_CHURCH_ID": 4,
    "DEFAULT_PHONE": "1",
    "DEFAULT_ROUNDUP_MULTIPLIER": 1.0,
    "DEFAULT_ROUNDUP_THRESHOLD": 1.0,
    "STRIPE_PROCESSING_FEE_RATE": 0.029,
    "STRIPE_PROCESSING_FEE_FIXED": 0.30,
    # Fallback spending category percentages (used when real transaction data is unavailable)
    "FALLBACK_FOOD_PERCENTAGE": 0.25,
    "FALLBACK_SHOPPING_PERCENTAGE": 0.30,
    "FALLBACK_TRANSPORT_PERCENTAGE": 0.15,
    "FALLBACK_ENTERTAINMENT_PERCENTAGE": 0.10,
    "FALLBACK_OTHER_PERCENTAGE": 0.20,
    # Payout processing constants
    "PAYOUT_HOLD_PERIOD_DAYS": 7,  # Hold donations for 7 days before payout
    "MIN_PAYOUT_AMOUNT": 1.00,  # Minimum payout amount ($1.00)
    # Referral commission constants
    "MIN_COMMISSION_PAYOUT": 5.0,  # Minimum commission amount for payout ($5.00)
    "COMMISSION_HOLD_DAYS": 30,  # Hold commissions for 30 days before payout
}

# ============================
# File Upload Constants
# ============================
FILE_CONSTANTS = {
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    "UPLOAD_DIR": "./uploads",
    "CHURCH_DOCS_DIR": "./uploads/church_docs",
    "ALLOWED_EXTENSIONS": [".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"],
}

# ============================
# Rate Limiting Constants
# ============================
RATE_LIMIT_CONSTANTS = {
    "DEFAULT": "100/minute",
    "AUTH": "5/minute",
    "REGISTER": "3/minute",
    "EMAIL_RESEND": "1/minute",
}

# Plaid API Rate Limiting
PLAID_RATE_LIMIT_DELAY = 1.0  # Base delay in seconds
PLAID_MAX_RETRIES = 3
PLAID_BACKOFF_MULTIPLIER = 2.0
PLAID_CACHE_TTL = 300  # 5 minutes cache TTL

# Plaid API Timeout Configuration
PLAID_TIMEOUT = 30  # 30 seconds timeout
PLAID_CONNECT_TIMEOUT = 10  # 10 seconds connection timeout
PLAID_READ_TIMEOUT = 30  # 30 seconds read timeout

# Business Constants
MAX_DONATION_AMOUNT = 50.0
STRIPE_PROCESSING_FEE_RATE = 0.029
STRIPE_PROCESSING_FEE_FIXED = 0.30

# ============================
# Security Constants
# ============================
SECURITY_CONSTANTS = {
    "BCRYPT_ROUNDS": 12,
    "SECRET_KEY_MIN_LENGTH": 32,
    "API_KEY_PREFIX": "manna_",
    "ACCESS_CODE_LENGTH": 16,
}

# ============================
# Database Constants
# ============================
DATABASE_CONSTANTS = {
    "POOL_SIZE": 10,
    "MAX_OVERFLOW": 20,
    "POOL_TIMEOUT": 30,
    "POOL_RECYCLE": 3600,
}

# ============================
# Email Constants
# ============================
EMAIL_CONSTANTS = {
    "FROM_EMAIL": "noreply@manna.com",
    "FROM_NAME": "Manna",
    "TEMPLATE_DIR": "templates/email",
}

# ============================
# Payment Constants
# ============================
PAYMENT_CONSTANTS = {
    "CURRENCY": "usd",
    "MIN_AMOUNT": 0.50,
    "MAX_AMOUNT": 10000.0,
    "DEFAULT_PAYMENT_METHOD": "card",
}

# ============================
# Test Mode Constants
# ============================
TEST_MODE_CONSTANTS = {
    "STRIPE_TEST_TOKEN": "tok_visa",
    "STRIPE_TEST_CARD": "4242424242424242",
    "STRIPE_TEST_CVC": "123",
    "STRIPE_TEST_EXPIRY": "12/25",
    "PLAID_TEST_ACCESS_TOKEN": "access-sandbox-test-token",
    "PLAID_TEST_ITEM_ID": "test-item-id",
}

# ============================
# Status Constants
# ============================
STATUS_CONSTANTS = {
    "SUCCESS": "success",
    "PENDING": "pending",
    "FAILED": "failed",
    "ACTIVE": "active",
    "INACTIVE": "inactive",
    "VERIFIED": "verified",
    "FLAGGED": "flagged",
    "APPROVED": "approved",
    "REJECTED": "rejected",
}

# ============================
# Frequency Constants
# ============================
FREQUENCY_CONSTANTS = {
    "MONTHLY": "monthly",
    "WEEKLY": "weekly",
    "DAILY": "daily",
    "BIWEEKLY": "biweekly",
}

# ============================
# Notification Constants
# ============================
NOTIFICATION_CONSTANTS = {
    "PUSH_ENABLED": True,
    "EMAIL_ENABLED": True,
    "SMS_ENABLED": False,
    "DEFAULT_CHANNEL": "email",
}

# ============================
# Helper Functions
# ============================

def get_auth_constant(key: str, default=None) -> int:
    """Get authentication constant as integer"""
    value = AUTH_CONSTANTS.get(key, default)
    if isinstance(value, (int, float)):
        return int(value)
    elif isinstance(value, str) and value.isdigit():
        return int(value)
    elif default is not None:
        return int(default) if isinstance(default, (int, float, str)) and str(default).isdigit() else 0
    return 0

def get_business_constant(key: str, default=None):
    """Get business logic constant"""
    return BUSINESS_CONSTANTS.get(key, default)

def get_file_constant(key: str, default=None):
    """Get file upload constant"""
    return FILE_CONSTANTS.get(key, default)

def get_rate_limit_constant(key: str, default=None):
    """Get rate limiting constant"""
    return RATE_LIMIT_CONSTANTS.get(key, default)

def get_security_constant(key: str, default=None):
    """Get security constant"""
    return SECURITY_CONSTANTS.get(key, default)

def get_database_constant(key: str, default=None):
    """Get database constant"""
    return DATABASE_CONSTANTS.get(key, default)

def get_email_constant(key: str, default=None):
    """Get email constant"""
    return EMAIL_CONSTANTS.get(key, default)

def get_payment_constant(key: str, default=None):
    """Get payment constant by key"""
    return PAYMENT_CONSTANTS.get(key, default)

def get_notification_constant(key: str, default=None):
    """Get notification constant by key"""
    return NOTIFICATION_CONSTANTS.get(key, default)

def get_test_mode_constant(key: str, default=None):
    """Get test mode constant by key"""
    return TEST_MODE_CONSTANTS.get(key, default)

def get_status_constant(key: str, default=None):
    """Get status constant by key"""
    return STATUS_CONSTANTS.get(key, default)

def get_frequency_constant(key: str, default=None):
    """Get frequency constant by key"""
    return FREQUENCY_CONSTANTS.get(key, default)

# ============================
# Legacy Support Functions (for backward compatibility)
# ============================

def get_commission_rate():
    """Get referral commission rate"""
    return get_business_constant("REFERRAL_COMMISSION_RATE", 0.10)

def get_default_roundup_multiplier():
    """Get default roundup multiplier"""
    return get_business_constant("DEFAULT_ROUNDUP_MULTIPLIER", 1.0)

def get_default_roundup_threshold():
    """Get default roundup threshold"""
    return get_business_constant("DEFAULT_ROUNDUP_THRESHOLD", 1.0)

def get_max_donation_amount():
    """Get maximum donation amount"""
    return get_business_constant("MAX_DONATION_AMOUNT", 1000.0)

def get_default_church_id():
    """Get default church ID"""
    return get_business_constant("DEFAULT_CHURCH_ID", 4)

# ============================
# HTTP Status Constants
# ============================
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}

# ============================
# Error Message Constants
# ============================
ERROR_MESSAGES = {
    "AUTH_TOKEN_INVALID": "Invalid or expired token",
    "AUTH_ROLE_FORBIDDEN": "Insufficient permissions",
    "AUTH_LOGIN_FAILED": "Invalid credentials",
    "USER_REGISTER_EXISTS": "User already exists",
    "DB_ERROR": "Database error occurred",
    "PAYMENT_FAILED": "Payment processing failed",
    "EMAIL_SEND_FAILED": "Failed to send email",
    "ACCESS_CODE_INVALID": "Invalid access code"
} 
