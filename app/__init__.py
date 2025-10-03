"""
Manna Backend API

A FastAPI-based backend for the Manna donation platform.
Provides authentication, banking integration, church management, and donation processing.

Author: Manna Development Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Manna Development Team"
__description__ = "FastAPI backend for Manna donation platform"

# Main application imports
from app.main import app
from app.config import config

# Core utilities
from app.utils.database import get_db, database, engine, SessionLocal, Base

# Core responses
from app.core.responses import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    AuthTokenResponse,
    ResponseFactory
)

# Core messages
from app.core.messages import get_auth_message, get_bank_message, get_church_message

# Main exports
__all__ = [
    # Application
    "app",
    "config",
    
    # Database
    "get_db",
    "database", 
    "engine",
    "SessionLocal",
    "Base",
    
    # Responses
    "BaseResponse",
    "SuccessResponse", 
    "ErrorResponse",
    "PaginatedResponse",
    "AuthTokenResponse",
    "ResponseFactory",
    
    # Messages
    "get_auth_message",
    "get_bank_message", 
    "get_church_message",
    
    # Constants - moved to core.constants
    # "get_constant",
    # "get_database_url",
    # "get_secret_key",
    
    # Version info
    "__version__",
    "__author__",
    "__description__"
]
