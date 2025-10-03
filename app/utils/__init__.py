"""
Utility functions and helpers for the Manna Backend API.

This package contains all utility functions for:
- Security (password hashing, JWT handling)
- Database operations
- Email sending
- Encryption/decryption
- Audit logging
- Notifications
- Constants management
"""

# Security utilities
from app.utils.security import (
    hash_password,
    verify_password,
    generate_access_code,
    SecurityManager
)

# JWT utilities
from app.utils.jwt_handler import (
    create_access_token,
    verify_access_token,
    create_refresh_token,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)

# Database utilities
from app.utils.database import (
    get_db,
    database,
    engine,
    SessionLocal,
    Base,
    db_session
)

# Email utilities
from app.utils.send_email import send_email_with_sendgrid

# Encryption utilities
from app.utils.encryption import (
    encrypt_data,
    decrypt_data,
    encrypt_token,
    decrypt_token
)

# Audit utilities
from app.utils.audit import log_audit_event

# Notification utilities
from app.utils.notifier import notify_church

# Constants utilities - moved to core.constants
# from .constants import (
#     get_constant,
#     get_database_url,
#     get_secret_key,
#     get_plaid_config,
#     get_stripe_config,
#     get_email_config
# )

# External service clients
from app.utils.stripe_client import stripe

# Main exports
__all__ = [
    # Security
    "hash_password",
    "verify_password", 
    "generate_access_code",
    "SecurityManager",
    
    # JWT
    "create_access_token",
    "verify_access_token",
    "create_refresh_token",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    
    # Database
    "get_db",
    "database",
    "engine", 
    "SessionLocal",
    "Base",
    "db_session",
    
    # Email
    "send_email_with_sendgrid",
    
    # Encryption
    "encrypt_data",
    "decrypt_data",
    "encrypt_token",
    "decrypt_token",
    
    # Audit
    "log_audit_event",
    
    # Notifications
    "notify_church",
    
    # Constants - moved to core.constants
    # "get_constant",
    # "get_database_url",
    # "get_secret_key",
    # "get_plaid_config",
    # "get_stripe_config",
    # "get_email_config",
    
    # External clients
    "stripe"
]
