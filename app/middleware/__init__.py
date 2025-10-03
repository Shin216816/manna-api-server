"""
Middleware components for the Manna Backend API.

This package contains all FastAPI middleware for:
- Authentication and authorization
- Request/response processing
- Security and validation
- Logging and monitoring
"""

# Authentication middleware
from app.middleware.auth_middleware import jwt_auth
from app.middleware.church_admin_auth import church_admin_auth
from app.middleware.admin_auth import admin_auth

# Main exports
__all__ = [
    # Authentication middleware
    "jwt_auth",
    "church_admin_auth",
    "admin_auth"
]
