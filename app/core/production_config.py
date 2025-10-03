"""
Production Configuration

Comprehensive production settings including:
- Security configurations
- Performance optimizations
- Monitoring settings
- Backup configurations
- Cache settings
- Notification settings
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field

class ProductionConfig(BaseSettings):
    """Production configuration settings"""
    
    # Application settings
    APP_NAME: str = "Manna - Micro-Donation Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    RATE_LIMIT_DEFAULT: int = 100  # requests per minute
    RATE_LIMIT_AUTH: int = 10  # auth attempts per minute
    RATE_LIMIT_API: int = 1000  # API calls per hour
    RATE_LIMIT_DONATION: int = 20  # donations per minute
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    CACHE_DEFAULT_TTL: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000
    CACHE_COMPRESSION: bool = True
    
    # Monitoring settings
    MONITORING_ENABLED: bool = True
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 60  # seconds
    ALERT_EMAIL: Optional[str] = Field(None, env="ALERT_EMAIL")
    
    # Notification settings
    NOTIFICATIONS_ENABLED: bool = True
    EMAIL_ENABLED: bool = True
    SMS_ENABLED: bool = False
    PUSH_NOTIFICATIONS_ENABLED: bool = True
    
    # Email settings
    SENDGRID_API_KEY: Optional[str] = Field(None, env="SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: str = "noreply@manna.com"
    EMAIL_TEMPLATES_DIR: str = "app/templates/email"
    
    # SMS settings
    TWILIO_ACCOUNT_SID: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = Field(None, env="TWILIO_PHONE_NUMBER")
    
    # Backup settings
    BACKUP_ENABLED: bool = True
    BACKUP_DIR: str = "/app/backups"
    BACKUP_RETENTION_DAILY: int = 30
    BACKUP_RETENTION_WEEKLY: int = 12
    BACKUP_RETENTION_MONTHLY: int = 12
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "text/plain"
    ]
    UPLOAD_DIR: str = "/app/uploads"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "https://manna-frontend.vercel.app",
        "https://manna.com",
        "https://www.manna.com"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Trusted hosts
    TRUSTED_HOSTS: List[str] = [
        "manna-api-server.onrender.com",
        "api.manna.com",
        "localhost",
        "127.0.0.1"
    ]
    
    # Security headers
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    CSP_ENABLED: bool = True
    XSS_PROTECTION: bool = True
    CONTENT_TYPE_NOSNIFF: bool = True
    FRAME_OPTIONS: str = "DENY"
    
    # Session settings
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "strict"
    SESSION_TIMEOUT: int = 3600  # 1 hour
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "/app/logs/app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Performance settings
    WORKERS: int = 4
    WORKER_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 5
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 100
    
    
    # External service settings
    PLAID_CLIENT_ID: str = Field(..., env="PLAID_CLIENT_ID")
    PLAID_SECRET: str = Field(..., env="PLAID_SECRET")
    PLAID_ENVIRONMENT: str = "production"
    
    STRIPE_PUBLISHABLE_KEY: str = Field(..., env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY: str = Field(..., env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(..., env="STRIPE_WEBHOOK_SECRET")
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: Optional[str] = None  # Disable in production
    API_REDOC_URL: Optional[str] = None  # Disable in production
    
    # Health check settings
    HEALTH_CHECK_PATH: str = "/health"
    HEALTH_CHECK_DETAILED_PATH: str = "/health/detailed"
    HEALTH_CHECK_TIMEOUT: int = 30
    
    # Metrics settings
    METRICS_PATH: str = "/metrics"
    METRICS_ENABLED: bool = True
    METRICS_INTERVAL: int = 60  # seconds
    
    # Alert thresholds
    CPU_THRESHOLD: float = 80.0
    MEMORY_THRESHOLD: float = 85.0
    DISK_THRESHOLD: float = 90.0
    ERROR_RATE_THRESHOLD: float = 5.0
    RESPONSE_TIME_THRESHOLD: float = 2.0
    
    # Feature flags
    FEATURE_ROUNDUPS: bool = True
    FEATURE_REFERRALS: bool = True
    FEATURE_NOTIFICATIONS: bool = True
    FEATURE_ANALYTICS: bool = True
    FEATURE_BACKUP: bool = True
    FEATURE_CACHE: bool = True
    FEATURE_MONITORING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global production config instance
production_config = ProductionConfig()

def get_production_config() -> ProductionConfig:
    """Get production configuration instance"""
    return production_config
