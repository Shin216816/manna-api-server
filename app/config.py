"""
Configuration management for Manna application.
Extracts constants from environment variables and integrates with centralized constants system.
"""

import os
import json
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path
from app.core.constants import (
    get_business_constant, get_auth_constant, get_file_constant,
    get_rate_limit_constant, get_security_constant, get_database_constant,
    get_email_constant, get_payment_constant, get_notification_constant,
    get_test_mode_constant, get_status_constant, get_frequency_constant
)

# Get the project root directory (where .env file should be located)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Load environment variables from .env file with explicit path
print(f"Loading environment from: {ENV_FILE_PATH}")
if ENV_FILE_PATH.exists():
    load_dotenv(dotenv_path=ENV_FILE_PATH)
    print(f"Environment file loaded successfully from: {ENV_FILE_PATH}")
else:
    print(f"Environment file not found at: {ENV_FILE_PATH}")
    print("Loading from default environment variables...")
    load_dotenv()  # Try to load from current directory

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", arbitrary_types_allowed=True, extra="ignore")
    # ============================
    # Environment Configuration
    # ============================
    APP_NAME: str = Field(default="Manna API", description="Application name")
    VERSION: str = Field(default="2.0.0", description="Application version")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")
    MODE: str = Field(default="test", description="Application mode (test, production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    SECRET_KEY: str = Field(default="", description="Secret key for JWT tokens")
    FERNET_SECRET: str = Field(default="", description="Fernet key for encryption")
    BASE_URL: str = Field(default="http://localhost:8000", description="Base URL for the API server")
    ADMIN_FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL for admin platform")
    
    # ============================
    # Database Configuration
    # ============================
    DATABASE_URL: Optional[str] = Field(default=None, description="Full database URL (for NeonDB)")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_NAME: str = Field(default="manna_db", description="Database name")
    DB_USER: str = Field(default="postgres", description="Database user")
    DB_PASSWORD: str = Field(default="", description="Database password")
    DB_POOL_SIZE: int = Field(default=20, description="Database pool size")
    DB_MAX_OVERFLOW: int = Field(default=30, description="Database max overflow")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Database pool recycle")
    DB_POOL_PRE_PING: bool = Field(default=True, description="Database pool pre ping")
    
    # ============================
    # Plaid Configuration
    # ============================
    PLAID_CLIENT_ID: str = Field(default="", description="Plaid client ID")
    PLAID_SECRET: str = Field(default="", description="Plaid secret")
    PLAID_ENV: str = Field(default="sandbox", description="Plaid environment")
    
    # ============================
    # Stripe Configuration
    # ============================
    STRIPE_SECRET_KEY: str = Field(default="", description="Stripe secret key")
    STRIPE_PUBLIC_KEY: str = Field(default="", description="Stripe public key")
    STRIPE_WEBHOOK_SECRET: str = Field(default="", description="Stripe webhook secret")
    STRIPE_CURRENCY: str = Field(default="USD", description="Stripe currency")
    
    # ============================
    # OAuth Configuration
    # ============================
    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", description="Google OAuth client secret")
    GOOGLE_REDIRECT_URI: str = Field(default="", description="Google OAuth redirect URI")

    # Apple OAuth
    APPLE_CLIENT_ID: Optional[str] = Field(default=None, description="Apple OAuth client ID")
    APPLE_TEAM_ID: Optional[str] = Field(default=None, description="Apple team ID")
    APPLE_KEY_ID: Optional[str] = Field(default=None, description="Apple key ID")
    APPLE_PRIVATE_KEY: Optional[str] = Field(default=None, description="Apple private key")
    APPLE_REDIRECT_URI: Optional[str] = Field(default=None, description="Apple OAuth redirect URI")

    # ============================
    # Database Notification Configuration
    # ============================
    # Firebase configuration removed - using database-based notification system
    # Notifications are handled through ChurchMessage, UserMessage, and AuditLog models

    # ============================
    # CORS and Security Headers Configuration
    # ============================
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS allowed origins")
    CORS_METHODS: List[str] = Field(default=["GET","POST","PUT","DELETE","OPTIONS","PATCH"], description="CORS allowed methods")
    CORS_HEADERS: List[str] = Field(default=["Accept","Accept-Language","Content-Language","Content-Type","Authorization","X-Requested-With","Origin","Access-Control-Request-Method","Access-Control-Request-Headers","X-API-Key","X-Client-Version","User-Agent"], description="CORS allowed headers")
    CORS_EXPOSE_HEADERS: List[str] = Field(default=["Content-Length","Content-Type","X-Total-Count","X-Page-Count"], description="CORS expose headers")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="CORS allow credentials")
    CORS_MAX_AGE: int = Field(default=86400, description="CORS max age in seconds")
    CORS_DEBUG: bool = Field(default=False, description="CORS debug mode")
    CORS_PREFLIGHT_CACHE_TIME: int = Field(default=86400, description="CORS preflight cache time")
    CORS_ERROR_HANDLING: bool = Field(default=True, description="CORS error handling")
    CORS_LOG_REQUESTS: bool = Field(default=False, description="CORS log requests")
    CORS_SECURITY_HEADERS: bool = Field(default=True, description="CORS security headers")
    CORS_RATE_LIMIT: str = Field(default="100/minute", description="CORS rate limit")
    CORS_HEALTH_CHECK_ENABLED: bool = Field(default=True, description="CORS health check enabled")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Allowed hosts")

    # ============================
    # Email Configuration
    # ============================
    EMAIL_FROM: str = Field(default=str(get_email_constant("FROM_EMAIL") or "noreply@manna.com"), description="From email address")
    EMAIL_FROM_NAME: str = Field(default=str(get_email_constant("FROM_NAME") or "Manna"), description="From name")
    SENDGRID_API_KEY: str = Field(default="", description="SendGrid API key")
    SENDGRID_USERNAME: str = Field(default="", description="SendGrid username")
    SENDGRID_PASSWORD: str = Field(default="", description="SendGrid password")
    SENDGRID_FROM_EMAIL: str = Field(default="", description="SendGrid from email")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USERNAME: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    
    # ============================
    # SMS Configuration (Twilio)
    # ============================
    TWILIO_ACCOUNT_SID: str = Field(default="", description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", description="Twilio Auth Token")
    TWILIO_PHONE_NUMBER: str = Field(default="", description="Twilio phone number")
    TWILIO_VERIFY_SERVICE_SID: str = Field(default="", description="Twilio Verify Service SID (optional)")
    
    # ============================
    # Business Logic Constants 
    # ============================
    REFERRAL_COMMISSION_RATE: float = Field(default=0.10, description="Referral commission rate")
    DEFAULT_DONATION_MULTIPLIER: float = Field(default=1.0, description="Default donation multiplier")
    MAX_DONATION_AMOUNT: float = Field(default=1000.0, description="Maximum donation amount")
    DEFAULT_CHURCH_ID: int = Field(default=4, description="Default church ID")
    DEFAULT_PHONE: str = Field(default="1", description="Default phone number")
    DEFAULT_ROUNDUP_MULTIPLIER: float = Field(default=1.0, description="Default roundup multiplier")
    DEFAULT_ROUNDUP_THRESHOLD: float = Field(default=1.0, description="Default roundup threshold")
    
    # Fallback spending category percentages (used when real transaction data is unavailable)
    FALLBACK_FOOD_PERCENTAGE: float = Field(default=0.25, description="Fallback food & dining percentage")
    FALLBACK_SHOPPING_PERCENTAGE: float = Field(default=0.30, description="Fallback shopping percentage")
    FALLBACK_TRANSPORT_PERCENTAGE: float = Field(default=0.15, description="Fallback transportation percentage")
    FALLBACK_ENTERTAINMENT_PERCENTAGE: float = Field(default=0.10, description="Fallback entertainment percentage")
    FALLBACK_OTHER_PERCENTAGE: float = Field(default=0.20, description="Fallback other categories percentage")

    # ============================
    # File Upload Configuration
    # ============================
    MAX_FILE_SIZE: int = Field(default=10485760, description="Maximum file size (10MB)")
    UPLOAD_DIR: str = Field(default="./uploads", description="Upload directory")
    CHURCH_DOCS_DIR: str = Field(default="./uploads/church_docs", description="Church documents directory")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(default=[".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"], description="Allowed file extensions")

    # ============================
    # Logging Configuration
    # ============================
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    LOG_MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Log max file size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Log backup count")

    # ============================
    # Security Constants
    # ============================
    BCRYPT_ROUNDS: int = Field(default=12, description="BCrypt rounds")
    SECRET_KEY_MIN_LENGTH: int = Field(default=32, description="Minimum secret key length")
    API_KEY_PREFIX: str = Field(default="manna_", description="API key prefix")
    ACCESS_CODE_LENGTH: int = Field(default=6, description="Access code length")

    # ============================
    # Rate Limiting
    # ============================
    RATE_LIMIT_DEFAULT: str = Field(default="100/minute", description="Default rate limit")
    RATE_LIMIT_AUTH: str = Field(default="5/minute", description="Auth rate limit")
    RATE_LIMIT_REGISTER: str = Field(default="3/minute", description="Register rate limit")
    RATE_LIMIT_EMAIL_RESEND: str = Field(default="1/minute", description="Email resend rate limit")

    # ============================
    # Database Pool Configuration
    # ============================
    DB_POOL_SIZE: int = Field(default=20, description="Database pool size")
    DB_MAX_OVERFLOW: int = Field(default=30, description="Database max overflow")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Database pool timeout")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Database pool recycle")

    # ============================
    # Notification Configuration
    # ============================
    PUSH_ENABLED: bool = Field(default=True, description="Push notifications enabled")
    EMAIL_ENABLED: bool = Field(default=True, description="Email notifications enabled")
    SMS_ENABLED: bool = Field(default=True, description="SMS notifications enabled")
    DEFAULT_NOTIFICATION_CHANNEL: str = Field(default="email", description="Default notification channel")

    # ============================
    # Payment Configuration
    # ============================
    PAYMENT_CURRENCY: str = Field(default="USD", description="Payment currency")
    PAYMENT_MIN_AMOUNT: float = Field(default=1.0, description="Minimum payment amount")
    PAYMENT_MAX_AMOUNT: float = Field(default=10000.0, description="Maximum payment amount")
    DEFAULT_PAYMENT_METHOD: str = Field(default="card", description="Default payment method")

    # ============================
    # Test Mode Configuration
    # ============================
    STRIPE_TEST_TOKEN: str = Field(default="tok_visa", description="Stripe test token for test mode")
    STRIPE_TEST_CARD: str = Field(default="4242424242424242", description="Stripe test card number")
    STRIPE_TEST_CVC: str = Field(default="123", description="Stripe test CVC")
    STRIPE_TEST_EXPIRY: str = Field(default="12/34", description="Stripe test expiry")
    PLAID_TEST_ACCESS_TOKEN: str = Field(default="access-sandbox-test", description="Plaid test access token")
    PLAID_TEST_ITEM_ID: str = Field(default="test-item-id", description="Plaid test item ID")

    # ============================
    # Status Configuration
    # ============================
    STATUS_SUCCESS: str = Field(default="success", description="Success status")
    STATUS_PENDING: str = Field(default="pending", description="Pending status")
    STATUS_FAILED: str = Field(default="failed", description="Failed status")
    STATUS_ACTIVE: str = Field(default="active", description="Active status")
    STATUS_INACTIVE: str = Field(default="inactive", description="Inactive status")
    STATUS_VERIFIED: str = Field(default="verified", description="Verified status")
    STATUS_FLAGGED: str = Field(default="flagged", description="Flagged status")
    STATUS_APPROVED: str = Field(default="approved", description="Approved status")
    STATUS_REJECTED: str = Field(default="rejected", description="Rejected status")

    # ============================
    # Frequency Configuration
    # ============================
    FREQUENCY_MONTHLY: str = Field(default="monthly", description="Monthly frequency")
    FREQUENCY_WEEKLY: str = Field(default="weekly", description="Weekly frequency")
    FREQUENCY_DAILY: str = Field(default="daily", description="Daily frequency")
    FREQUENCY_BIWEEKLY: str = Field(default="biweekly", description="Biweekly frequency")

    # ============================
    # Authentication Configuration
    # ============================
    TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expire minutes")
    EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Email verify token expire minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token expire days")
    ACCESS_CODE_EXPIRE_SECONDS: int = Field(default=60, description="Access code expire seconds")
    ACCESS_CODE_RESEND_COOLDOWN_SECONDS: int = Field(default=60, description="Access code resend cooldown seconds")
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Password minimum length")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRES_IN_SECONDS: int = Field(default=1800, description="JWT expires in seconds")
    JWT_TOKEN_TYPE: str = Field(default="bearer", description="JWT token type")
    JWT_AUDIENCE: List[str] = Field(default=["manna-users", "manna-refresh"], description="JWT audience")
    
    # ============================
    # Admin Configuration
    # ============================
    ADMIN_REGISTRATION_CODE: str = Field(default="MANNA_ADMIN_2024", description="Registration code required for admin signup")

    # ============================
    # Validation Methods
    # ============================

    @field_validator('REFERRAL_COMMISSION_RATE')
    @staticmethod
    def validate_commission_rate(v):
        """Validate commission rate"""
        if not 0 <= v <= 1:
            raise ValueError('REFERRAL_COMMISSION_RATE must be between 0 and 1')
        return v

    @field_validator('MAX_DONATION_AMOUNT')
    @staticmethod
    def validate_max_donation(v):
        """Validate maximum donation amount"""
        if v <= 0:
            raise ValueError('MAX_DONATION_AMOUNT must be positive')
        return v

    @field_validator('CORS_ORIGINS', 'ALLOWED_HOSTS', 'ALLOWED_FILE_EXTENSIONS', 'CORS_METHODS', 'CORS_HEADERS', 'CORS_EXPOSE_HEADERS', 'JWT_AUDIENCE', mode="before")
    @staticmethod
    def parse_list_fields(v):
        """Parse list fields from environment variables"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Handle comma-separated strings
                return [item.strip() for item in v.split(',') if item.strip()]
        return v

    @field_validator('BCRYPT_ROUNDS')
    @staticmethod
    def validate_bcrypt_rounds(v):
        """Validate BCrypt rounds"""
        if not 4 <= v <= 31:
            raise ValueError('BCRYPT_ROUNDS must be between 4 and 31')
        return v

    @field_validator('PASSWORD_MIN_LENGTH')
    @staticmethod
    def validate_password_min_length(v):
        """Validate password minimum length"""
        if v < 4:
            raise ValueError('PASSWORD_MIN_LENGTH must be at least 4')
        return v

    @field_validator('FERNET_SECRET')
    @staticmethod
    def validate_fernet_secret(v):
        """Validate Fernet secret key"""
        if not v:
            raise ValueError('FERNET_SECRET is required')
        try:
            from cryptography.fernet import Fernet
            Fernet(v.encode())
        except Exception as e:
            raise ValueError(f'Invalid FERNET_SECRET: {e}')
        return v

    # ============================
    # Computed Properties
    # ============================
    
    @property
    def get_database_url(self) -> str:
        """Generate database URL from components or use provided DATABASE_URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Generate async database URL from components or use provided DATABASE_URL"""
        if self.DATABASE_URL:
            # Convert postgresql:// to postgresql+asyncpg:// for async
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def IS_TEST_MODE(self) -> bool:
        """Check if running in test mode"""
        return self.MODE.lower() == "test"

    @property
    def IS_PRODUCTION_MODE(self) -> bool:
        """Check if running in production mode"""
        return self.MODE.lower() == "production"

    # ============================
    # Methods
    # ============================
    
    def validate_critical_settings(self):
        """Validate critical settings for production"""
        if self.IS_PRODUCTION:
            critical_settings = [
                "SECRET_KEY",
                "FERNET_SECRET",
                "STRIPE_SECRET_KEY",
                "PLAID_CLIENT_ID",
                "PLAID_SECRET"
            ]
            
            missing_settings = []
            for setting in critical_settings:
                if not getattr(self, setting, None):
                    missing_settings.append(setting)
            
            if missing_settings:
                raise ValueError(f"Missing critical settings for production: {', '.join(missing_settings)}")

    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration based on environment"""
        if self.IS_PRODUCTION:
            return {
                "allow_origins": [
                    "https://manna-api-server.onrender.com",
                    "https://swagger.io",
                    "https://editor.swagger.io",
                    "https://docs.manna.com"
                ],
                "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
                "allow_methods": self.CORS_METHODS,
                "allow_headers": self.CORS_HEADERS,
                "expose_headers": self.CORS_EXPOSE_HEADERS,
                "max_age": self.CORS_MAX_AGE
            }
        else:  # development
            return {
                "allow_origins": [
                    "http://localhost:3000",
                    "http://localhost:5173",  # Vite dev server
                    "http://localhost:8080", 
                    "http://localhost:4200",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",  # Vite dev server
                    "http://127.0.0.1:8080",
                    "http://127.0.0.1:4200",
                    "https://manna-api-server.onrender.com",
                    "https://swagger.io",
                    "https://editor.swagger.io",
                    "*"  # Allow all origins for development
                ],
                "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
                "allow_methods": self.CORS_METHODS,
                "allow_headers": self.CORS_HEADERS,
                "expose_headers": self.CORS_EXPOSE_HEADERS,
                "max_age": self.CORS_MAX_AGE
            }

    def get_constants_dict(self) -> Dict[str, Any]:
        """Get basic constants as a dictionary"""
        return {
            "AUTH_CONSTANTS": {
                "TOKEN_EXPIRE_MINUTES": self.TOKEN_EXPIRE_MINUTES,
                "EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES": self.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES,
                "REFRESH_TOKEN_EXPIRE_DAYS": self.REFRESH_TOKEN_EXPIRE_DAYS,
                "ACCESS_CODE_EXPIRE_SECONDS": self.ACCESS_CODE_EXPIRE_SECONDS,
                "ACCESS_CODE_RESEND_COOLDOWN_SECONDS": self.ACCESS_CODE_RESEND_COOLDOWN_SECONDS,
                "PASSWORD_MIN_LENGTH": self.PASSWORD_MIN_LENGTH,
                "JWT_ALGORITHM": self.JWT_ALGORITHM,
                "JWT_EXPIRES_IN_SECONDS": self.JWT_EXPIRES_IN_SECONDS,
                "JWT_TOKEN_TYPE": self.JWT_TOKEN_TYPE,
                "JWT_AUDIENCE": self.JWT_AUDIENCE,
            },
            "BUSINESS_CONSTANTS": {
                "REFERRAL_COMMISSION_RATE": self.REFERRAL_COMMISSION_RATE,
                "DEFAULT_DONATION_MULTIPLIER": self.DEFAULT_DONATION_MULTIPLIER,
                "MAX_DONATION_AMOUNT": self.MAX_DONATION_AMOUNT,
                "DEFAULT_CHURCH_ID": self.DEFAULT_CHURCH_ID,
                "DEFAULT_PHONE": self.DEFAULT_PHONE,
                "DEFAULT_ROUNDUP_MULTIPLIER": self.DEFAULT_ROUNDUP_MULTIPLIER,
                "DEFAULT_ROUNDUP_THRESHOLD": self.DEFAULT_ROUNDUP_THRESHOLD,
            },
            "EXTERNAL_SERVICE_CONSTANTS": {
                "PLAID_ENVIRONMENTS": ["sandbox", "development", "production"],
                "STRIPE_CURRENCY": self.STRIPE_CURRENCY,
                "EMAIL_PROVIDERS": ["sendgrid"],
                "OAUTH_PROVIDERS": ["google", "apple"],
            },
        }

    def update_centralized_constants(self):
        """Update centralized constants with environment values"""
        # This method is no longer needed as constants are now accessed via helper functions
        # The constants are now centralized and accessed through get_*_constant functions
        pass

    def print_config_summary(self):
        """Print a summary of the current configuration"""
        print("\n" + "="*60)
        print("MANNA CONFIGURATION SUMMARY")
        print("="*60)
        print(f"App: {self.APP_NAME} v{self.VERSION}")
        print(f"Environment: {self.ENVIRONMENT}")
        print(f"Mode: {self.MODE}")
        print(f"Debug: {self.DEBUG}")
        print(f"Host: {self.HOST}:{self.PORT}")
        print(f"Secret Key: {self.SECRET_KEY[:20]}..." if len(self.SECRET_KEY) > 20 else f"Secret Key: {self.SECRET_KEY}")
        print(f"Fernet Key: {self.FERNET_SECRET[:20]}..." if len(self.FERNET_SECRET) > 20 else f"Fernet Key: {self.FERNET_SECRET}")
        print(f"Database: {self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
        print(f"Email From: {self.EMAIL_FROM}")
        print(f"Stripe Currency: {self.STRIPE_CURRENCY}")
        print(f"Plaid Environment: {self.PLAID_ENV}")
        print(f"Commission Rate: {self.REFERRAL_COMMISSION_RATE}")
        print(f"Upload Dir: {self.UPLOAD_DIR}")
        print(f"CORS Origins: {self.CORS_ORIGINS}")
        print(f"CORS Debug: {self.CORS_DEBUG}")
        print("="*60)

# NOTE: All sensitive and environment-specific values (DB, Plaid, Stripe, etc.) must be set in .env
# Remove default values for secrets/keys to avoid masking missing .env values

# Example for secrets/keys (remove default):
# PLAID_CLIENT_ID: str = Field(..., description="Plaid client ID")
# PLAID_SECRET: str = Field(..., description="Plaid secret")
# SECRET_KEY: str = Field(..., description="Secret key for JWT")


# Create config instance
print("Initializing Manna configuration...")
config = Config()

# Print configuration summary
config.print_config_summary()

# Validate settings on import
if config.IS_PRODUCTION:
    print("Production environment detected - validating critical settings...")
    config.validate_critical_settings()
    print("Production validation passed")

# Update centralized constants with environment values
print("Updating centralized constants with environment values...")
config.update_centralized_constants()
print("Centralized constants updated")

# Export config for easy access
__all__ = ["config"]

print("Configuration initialization complete!")
