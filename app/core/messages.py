"""
Centralized message content system for all controllers and functions.
Provides consistent, maintainable message strings across the application.
"""

# ============================
# Authentication Messages
# ============================

AUTH_MESSAGES = {
    # Registration
    "REGISTER_SUCCESS": "User registration successful",
    "REGISTER_FAILED": "User registration failed",
    "REGISTER_USER_EXISTS": "User already exists with this email",
    "REGISTER_INVALID_EMAIL": "Invalid email format",
    "REGISTER_INVALID_PHONE": "Invalid phone number format",
    "REGISTER_EMAIL_OR_PHONE_REQUIRED": "Email or phone number is required",
    "REGISTER_PASSWORD_TOO_WEAK": "Password must be at least 6 characters long",
    "REGISTER_PASSWORD_MISMATCH": "Passwords do not match",
    "REGISTER_ACCESS_CODE_SENT": "Access code sent successfully",
    "REGISTER_ACCESS_CODE_INVALID": "Invalid access code",
    "REGISTER_ACCESS_CODE_EXPIRED": "Access code has expired",
    "REGISTER_ACCESS_CODE_CONFIRMED": "Access code confirmed successfully",
    "REGISTER_ACCESS_CODE_RESEND_SUCCESS": "Access code resent successfully",
    "REGISTER_ACCESS_CODE_RESEND_TOO_SOON": "Please wait before requesting another code",
    "REGISTER_ACCESS_CODE_RESENT": "Access code resent successfully",
    "REGISTER_ACCESS_CODE_RESEND_FAILED": "Failed to resend access code",
    
    # Login
    "LOGIN_SUCCESS": "Login successful",
    "LOGIN_FAILED": "Invalid credentials",
    "LOGIN_ERROR": "Login error occurred",
    "LOGIN_USER_NOT_FOUND": "User not found",
    "LOGIN_ACCOUNT_DISABLED": "Account is disabled",
    "LOGIN_ACCOUNT_INACTIVE": "Account is inactive",
    "LOGIN_TOO_MANY_ATTEMPTS": "Too many login attempts. Please try again later",
    
    # Logout
    "LOGOUT_SUCCESS": "Logout successful",
    "LOGOUT_TOKEN_INVALID": "Invalid token",
    "LOGOUT_TOKEN_REVOKED": "Token has been revoked",
    
    # Password Management
    "PASSWORD_CHANGE_SUCCESS": "Password changed successfully",
    "PASSWORD_CHANGE_FAILED": "Password change failed",
    "PASSWORD_CHANGE_OLD_INCORRECT": "Current password is incorrect",
    "PASSWORD_CHANGE_MISMATCH": "New passwords do not match",
    "PASSWORD_RESET_SUCCESS": "Password reset successful",
    "PASSWORD_RESET_FAILED": "Password reset failed",
    "PASSWORD_RESET_CODE_INVALID": "Invalid reset code",
    "PASSWORD_RESET_CODE_EXPIRED": "Reset code has expired",
    "FORGOT_PASSWORD_SUCCESS": "Password reset instructions sent",
    "FORGOT_PASSWORD_FAILED": "Failed to send password reset instructions",
    "FORGOT_PASSWORD_USER_NOT_FOUND": "No account found with this email or phone number",
    
    # User Management
    "USER_NOT_FOUND": "User not found",
    
    # Token Management
    "TOKEN_REFRESH_SUCCESS": "Token refreshed successfully",
    "TOKEN_REFRESH_FAILED": "Token refresh failed",
    "TOKEN_REFRESH_ERROR": "Token refresh error occurred",
    "TOKEN_REFRESH_INVALID": "Invalid refresh token",
    "TOKEN_REFRESH_EXPIRED": "Refresh token has expired",
    "TOKEN_REFRESH_REVOKED": "Refresh token has been revoked",
    
    # OAuth
    "OAUTH_GOOGLE_SUCCESS": "Google authentication successful",
    "OAUTH_GOOGLE_FAILED": "Google authentication failed",
    "OAUTH_APPLE_SUCCESS": "Apple authentication successful",
    "OAUTH_APPLE_FAILED": "Apple authentication failed",
    "OAUTH_INVALID_CODE": "Invalid authorization code",
    "OAUTH_USER_EXISTS": "User already exists with this account",
}

# ============================
# Bank Integration Messages
# ============================

BANK_MESSAGES = {
    # Plaid Integration
    "PLAID_LINK_TOKEN_CREATED": "Plaid link token created successfully",
    "PLAID_LINK_TOKEN_FAILED": "Failed to create Plaid link token",
    "PLAID_PUBLIC_TOKEN_EXCHANGED": "Public token exchanged successfully",
    "PLAID_PUBLIC_TOKEN_EXCHANGE_FAILED": "Failed to exchange public token",
    "PLAID_ACCOUNTS_RETRIEVED": "Bank accounts retrieved successfully",
    "PLAID_ACCOUNTS_RETRIEVAL_FAILED": "Failed to retrieve bank accounts",
    "PLAID_TRANSACTIONS_RETRIEVED": "Transactions retrieved successfully",
    "PLAID_TRANSACTIONS_RETRIEVAL_FAILED": "Failed to retrieve transactions",
    "PLAID_USER_NOT_FOUND": "Plaid user not found",
    "PLAID_ACCOUNT_NOT_FOUND": "Bank account not found",
    # Added missing keys
    "BANK_ACCOUNT_NOT_FOUND": "Bank account not found",
    "TRANSACTIONS_FETCH_FAILED": "Failed to fetch transactions",
    "DONATION_BATCH_NOT_FOUND": "Donation batch not found",
    "DONATION_PREFERENCES_NOT_FOUND": "Donation preferences not found",
    # Donation Processing
    "DONATION_BATCH_CREATED": "Donation batch created successfully",
    "DONATION_BATCH_FAILED": "Failed to create donation batch",
    "DONATION_BATCH_EXECUTED": "Donation batch executed successfully",
    "DONATION_BATCH_EXECUTION_FAILED": "Failed to execute donation batch",
    "DONATION_CHARGED_SUCCESS": "Donation charged successfully",
    "DONATION_CHARGE_FAILED": "Failed to charge donation",
    "DONATION_HISTORY_RETRIEVED": "Donation history retrieved successfully",
    "DONATION_HISTORY_RETRIEVAL_FAILED": "Failed to retrieve donation history",
    "DONATION_SUMMARY_RETRIEVED": "Donation summary retrieved successfully",
    "DONATION_SUMMARY_RETRIEVAL_FAILED": "Failed to retrieve donation summary",
    "DONATION_PREFERENCES_UPDATED": "Donation preferences updated successfully",
    "DONATION_PREFERENCES_UPDATE_FAILED": "Failed to update donation preferences",
    "DONATION_SCHEDULE_CREATED": "Donation schedule created successfully",
    "DONATION_SCHEDULE_FAILED": "Failed to create donation schedule",
    "DONATION_SCHEDULE_UPDATED": "Donation schedule updated successfully",
    "DONATION_SCHEDULE_DELETED": "Donation schedule deleted successfully",
    # Roundup Calculations
    "ROUNDUP_CALCULATED": "Roundup amount calculated successfully",
    "ROUNDUP_CALCULATION_FAILED": "Failed to calculate roundup amount",
    "ROUNDUP_INSUFFICIENT_TRANSACTIONS": "Insufficient transactions for roundup calculation",
    # Stripe Integration
    "STRIPE_CHARGE_SUCCESS": "Stripe charge successful",
    "STRIPE_CHARGE_FAILED": "Stripe charge failed",
    "STRIPE_PAYMENT_METHOD_CREATED": "Payment method created successfully",
    "STRIPE_PAYMENT_METHOD_FAILED": "Failed to create payment method",
    "STRIPE_INSUFFICIENT_FUNDS": "Insufficient funds for transaction",
    "STRIPE_CARD_DECLINED": "Card was declined",
    "STRIPE_INVALID_CARD": "Invalid card information",
    # Add missing link token create failed key
    "LINK_TOKEN_CREATE_FAILED": "Failed to create Plaid link token."
}

# ============================
# Church Management Messages
# ============================

CHURCH_MESSAGES = {
    # Church Registration
    "CHURCH_REGISTER_SUCCESS": "Church registration successful",
    "CHURCH_REGISTER_FAILED": "Church registration failed",
    "CHURCH_REGISTER_EXISTS": "Church already exists",
    "CHURCH_REGISTER_INVALID_DATA": "Invalid church registration data",
    
    # Church Admin
    "CHURCH_ADMIN_LOGIN_SUCCESS": "Church admin login successful",
    "CHURCH_ADMIN_LOGIN_FAILED": "Church admin login failed",
    "CHURCH_ADMIN_NOT_FOUND": "Church admin not found",
    "CHURCH_ADMIN_INVALID_CREDENTIALS": "Invalid church admin credentials",
    "CHURCH_ADMIN_ACCOUNT_DISABLED": "Church admin account is disabled",
    
    # Church Management
    "CHURCH_PROFILE_UPDATED": "Church profile updated successfully",
    "CHURCH_PROFILE_UPDATE_FAILED": "Failed to update church profile",
    "CHURCH_STATUS_TOGGLED": "Church status updated successfully",
    "CHURCH_STATUS_TOGGLE_FAILED": "Failed to update church status",
    "CHURCH_NOT_FOUND": "Church not found",
    "CHURCH_DISABLED": "Church is currently disabled",
    
    # KYC Documents
    "KYC_UPLOAD_SUCCESS": "KYC document uploaded successfully",
    "KYC_UPLOAD_FAILED": "Failed to upload KYC document",
    "KYC_DOCUMENT_NOT_FOUND": "KYC document not found",
    "KYC_DOCUMENT_DELETED": "KYC document deleted successfully",
    "KYC_DOCUMENT_DELETE_FAILED": "Failed to delete KYC document",
    "KYC_INVALID_FILE_TYPE": "Invalid file type for KYC document",
    "KYC_FILE_TOO_LARGE": "KYC document file is too large",
    
    # Church Notifications
    "CHURCH_NOTIFICATIONS_RETRIEVED": "Church notifications retrieved successfully",
    "CHURCH_NOTIFICATIONS_RETRIEVAL_FAILED": "Failed to retrieve church notifications",
    "CHURCH_NOTIFICATION_MARKED_READ": "Notification marked as read",
    "CHURCH_NOTIFICATION_MARK_READ_FAILED": "Failed to mark notification as read",
    
    # Church Referrals
    "CHURCH_REFERRAL_CREATED": "Church referral created successfully",
    "CHURCH_REFERRAL_FAILED": "Failed to create church referral",
    "CHURCH_REFERRAL_EXISTS": "Church referral already exists",
    "CHURCH_REFERRAL_NOT_FOUND": "Church referral not found",
    "CHURCH_REFERRAL_UPDATED": "Church referral updated successfully",
    "CHURCH_REFERRAL_DELETED": "Church referral deleted successfully",
}

# ============================
# Admin Panel Messages
# ============================

ADMIN_MESSAGES = {
    # Admin Authentication
    "ADMIN_LOGIN_SUCCESS": "Admin login successful",
    "ADMIN_LOGIN_FAILED": "Admin login failed",
    "ADMIN_LOGIN_INVALID": "Invalid admin credentials",
    "ADMIN_NOT_FOUND": "Admin user not found",
    "ADMIN_ACCOUNT_DISABLED": "Admin account is disabled",
    "ADMIN_INSUFFICIENT_PERMISSIONS": "Insufficient admin permissions",
    
    # Admin Operations
    "ADMIN_USER_CREATED": "Admin user created successfully",
    "ADMIN_USER_CREATION_FAILED": "Failed to create admin user",
    "ADMIN_USER_UPDATED": "Admin user updated successfully",
    "ADMIN_USER_UPDATE_FAILED": "Failed to update admin user",
    "ADMIN_USER_DELETED": "Admin user deleted successfully",
    "ADMIN_USER_DELETE_FAILED": "Failed to delete admin user",
    "ADMIN_USER_EXISTS": "Admin user already exists",
    
    # Platform Management
    "PLATFORM_STATS_RETRIEVED": "Platform statistics retrieved successfully",
    "PLATFORM_STATS_RETRIEVAL_FAILED": "Failed to retrieve platform statistics",
    "PLATFORM_SETTINGS_UPDATED": "Platform settings updated successfully",
    "PLATFORM_SETTINGS_UPDATE_FAILED": "Failed to update platform settings",
    
    # Referral Payouts
    "REFERRAL_PAYOUT_PROCESSED": "Referral payout processed successfully",
    "REFERRAL_PAYOUT_FAILED": "Failed to process referral payout",
    "REFERRAL_PAYOUT_INSUFFICIENT_FUNDS": "Insufficient funds for referral payout",
    "REFERRAL_PAYOUT_NOT_FOUND": "Referral payout not found",
    "REFERRAL_PAYOUT_ALREADY_PROCESSED": "Referral payout already processed",
    
    # Audit Logs
    "AUDIT_LOG_CREATED": "Audit log created successfully",
    "AUDIT_LOG_CREATION_FAILED": "Failed to create audit log",
    "AUDIT_LOGS_RETRIEVED": "Audit logs retrieved successfully",
    "AUDIT_LOGS_RETRIEVAL_FAILED": "Failed to retrieve audit logs",
}

# ============================
# Webhook Messages
# ============================

WEBHOOK_MESSAGES = {
    # Plaid Webhooks
    "PLAID_WEBHOOK_PROCESSED": "Plaid webhook processed successfully",
    "PLAID_WEBHOOK_FAILED": "Failed to process Plaid webhook",
    "PLAID_WEBHOOK_INVALID_SIGNATURE": "Invalid Plaid webhook signature",
    "PLAID_WEBHOOK_UNKNOWN_TYPE": "Unknown Plaid webhook type",
    
    # Stripe Webhooks
    "STRIPE_WEBHOOK_PROCESSED": "Stripe webhook processed successfully",
    "STRIPE_WEBHOOK_FAILED": "Failed to process Stripe webhook",
    "STRIPE_WEBHOOK_INVALID_SIGNATURE": "Invalid Stripe webhook signature",
    "STRIPE_WEBHOOK_UNKNOWN_TYPE": "Unknown Stripe webhook type",
    
    # General Webhook
    "WEBHOOK_RECEIVED": "Webhook received successfully",
    "WEBHOOK_PROCESSING_FAILED": "Webhook processing failed",
    "WEBHOOK_RETRY_SCHEDULED": "Webhook retry scheduled",
}

# ============================
# User Management Messages
# ============================

USER_MESSAGES = {
    # Profile Management
    "USER_PROFILE_RETRIEVED": "User profile retrieved successfully",
    "USER_PROFILE_RETRIEVAL_FAILED": "Failed to retrieve user profile",
    "USER_PROFILE_UPDATED": "User profile updated successfully",
    "USER_PROFILE_UPDATE_FAILED": "Failed to update user profile",
    "USER_PROFILE_NOT_FOUND": "User profile not found",
    
    # Account Management
    "USER_ACCOUNT_DELETED": "User account deleted successfully",
    "USER_ACCOUNT_DELETE_FAILED": "Failed to delete user account",
    "USER_ACCOUNT_DISABLED": "User account disabled successfully",
    "USER_ACCOUNT_ENABLED": "User account enabled successfully",
    "USER_ACCOUNT_STATUS_UPDATE_FAILED": "Failed to update user account status",
    
    # Preferences
    "USER_PREFERENCES_UPDATED": "User preferences updated successfully",
    "USER_PREFERENCES_UPDATE_FAILED": "Failed to update user preferences",
    "USER_PREFERENCES_RETRIEVED": "User preferences retrieved successfully",
    "USER_PREFERENCES_RETRIEVAL_FAILED": "Failed to retrieve user preferences",
}

# ============================
# System Messages
# ============================

SYSTEM_MESSAGES = {
    # Database Operations
    "DB_OPERATION_SUCCESS": "Database operation successful",
    "DB_OPERATION_FAILED": "Database operation failed",
    "DB_CONNECTION_ERROR": "Database connection error",
    "DB_TRANSACTION_FAILED": "Database transaction failed",
    
    # File Operations
    "FILE_UPLOAD_SUCCESS": "File uploaded successfully",
    "FILE_UPLOAD_FAILED": "File upload failed",
    "FILE_DELETE_SUCCESS": "File deleted successfully",
    "FILE_DELETE_FAILED": "File deletion failed",
    "FILE_NOT_FOUND": "File not found",
    "FILE_TOO_LARGE": "File size exceeds maximum limit",
    "FILE_INVALID_TYPE": "Invalid file type",
    
    # Email Operations
    "EMAIL_SENT_SUCCESS": "Email sent successfully",
    "EMAIL_SEND_FAILED": "Failed to send email",
    "EMAIL_TEMPLATE_NOT_FOUND": "Email template not found",
    "EMAIL_INVALID_RECIPIENT": "Invalid email recipient",
    
    # Validation
    "VALIDATION_SUCCESS": "Validation successful",
    "VALIDATION_FAILED": "Validation failed",
    "VALIDATION_INVALID_INPUT": "Invalid input data",
    "VALIDATION_MISSING_REQUIRED": "Missing required fields",
    
    # Rate Limiting
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please try again later",
    "RATE_LIMIT_RESET": "Rate limit will reset soon",
    
    # Security
    "SECURITY_ACCESS_DENIED": "Access denied",
    "SECURITY_INSUFFICIENT_PERMISSIONS": "Insufficient permissions",
    "SECURITY_INVALID_TOKEN": "Invalid security token",
    "SECURITY_TOKEN_EXPIRED": "Security token has expired",
    
    # General
    "OPERATION_SUCCESS": "Operation completed successfully",
    "OPERATION_FAILED": "Operation failed",
    "RESOURCE_NOT_FOUND": "Resource not found",
    "RESOURCE_ALREADY_EXISTS": "Resource already exists",
    "RESOURCE_CREATED": "Resource created successfully",
    "RESOURCE_UPDATED": "Resource updated successfully",
    "RESOURCE_DELETED": "Resource deleted successfully",
    "INTERNAL_SERVER_ERROR": "Internal server error",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
}

# ============================
# Message Categories
# ============================

MESSAGE_CATEGORIES = {
    "AUTH": AUTH_MESSAGES,
    "BANK": BANK_MESSAGES,
    "CHURCH": CHURCH_MESSAGES,
    "ADMIN": ADMIN_MESSAGES,
    "WEBHOOK": WEBHOOK_MESSAGES,
    "USER": USER_MESSAGES,
    "SYSTEM": SYSTEM_MESSAGES,
}

# ============================
# Message Helper Functions
# ============================

def get_message(category: str, key: str) -> str:
    """Get a message from the specified category and key"""
    if category not in MESSAGE_CATEGORIES:
        raise ValueError(f"Unknown message category: {category}")
    
    if key not in MESSAGE_CATEGORIES[category]:
        raise ValueError(f"Unknown message key: {key} in category: {category}")
    
    return MESSAGE_CATEGORIES[category][key]

def get_auth_message(key: str) -> str:
    """Get an authentication message"""
    return get_message("AUTH", key)

def get_bank_message(key: str) -> str:
    """Get a bank integration message"""
    return get_message("BANK", key)

def get_church_message(key: str) -> str:
    """Get a church management message"""
    return get_message("CHURCH", key)

def get_admin_message(key: str) -> str:
    """Get an admin panel message"""
    return get_message("ADMIN", key)

def get_webhook_message(key: str) -> str:
    """Get a webhook message"""
    return get_message("WEBHOOK", key)

def get_user_message(key: str) -> str:
    """Get a user management message"""
    return get_message("USER", key)

def get_system_message(key: str) -> str:
    """Get a system message"""
    return get_message("SYSTEM", key)

# ============================
# Message Formatting
# ============================

def format_message(message: str, **kwargs) -> str:
    """Format a message with dynamic values"""
    try:
        return message.format(**kwargs)
    except KeyError as e:
        # If formatting fails, return the original message
        return message

def format_auth_message(key: str, **kwargs) -> str:
    """Format an authentication message with dynamic values"""
    return format_message(get_auth_message(key), **kwargs)

def format_bank_message(key: str, **kwargs) -> str:
    """Format a bank message with dynamic values"""
    return format_message(get_bank_message(key), **kwargs)

def format_church_message(key: str, **kwargs) -> str:
    """Format a church message with dynamic values"""
    return format_message(get_church_message(key), **kwargs)

def format_admin_message(key: str, **kwargs) -> str:
    """Format an admin message with dynamic values"""
    return format_message(get_admin_message(key), **kwargs)

def format_webhook_message(key: str, **kwargs) -> str:
    """Format a webhook message with dynamic values"""
    return format_message(get_webhook_message(key), **kwargs)

def format_user_message(key: str, **kwargs) -> str:
    """Format a user message with dynamic values"""
    return format_message(get_user_message(key), **kwargs)

def format_system_message(key: str, **kwargs) -> str:
    """Format a system message with dynamic values"""
    return format_message(get_system_message(key), **kwargs) 
