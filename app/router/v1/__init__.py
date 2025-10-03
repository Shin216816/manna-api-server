"""
API Version 1 routers for the Manna Backend API.

This package contains all v1 API endpoints organized by functionality:
- Mobile app endpoints (Flutter)
- Church admin endpoints (Web app)
- Internal admin endpoints (Platform management)
- Shared endpoints (Common functionality)
"""

from fastapi import APIRouter

# Import individual routers
from app.router.v1.mobile import mobile_router
from app.router.v1.church import church_router
from app.router.v1.admin import admin_router
from app.router.v1.donor import donor_router
from app.router.v1.shared import shared_router
from app.router.v1.auth import oauth_router
from app.router.v1.public import public_router

# Create main v1 router
v1_router = APIRouter()

# Include all sub-routers with appropriate prefixes and tags
v1_router.include_router(
    mobile_router, 
    prefix="/mobile", 
    tags=["Mobile App"]
)

v1_router.include_router(
    church_router, 
    prefix="/church", 
    tags=["Church Management"]
)

v1_router.include_router(
    admin_router, 
    prefix="/admin", 
    tags=["Admin Platform"]
)

v1_router.include_router(
    donor_router, 
    prefix="/donor", 
    tags=["Donor Web App"]
)

v1_router.include_router(
    shared_router, 
    prefix="/shared", 
    tags=["Shared Services"]
)

v1_router.include_router(
    oauth_router, 
    prefix="/auth", 
    tags=["OAuth Authentication"]
)

v1_router.include_router(
    public_router, 
    prefix="/public", 
    tags=["Public API"]
)

# Main exports
__all__ = [
    "v1_router",
    "mobile_router",
    "church_router", 
    "admin_router",
    "donor_router",
    "shared_router",
    "oauth_router",
    "public_router"
]
