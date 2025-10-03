"""
API routers for the Manna Backend API.

This package contains all FastAPI routers for:
- API versioning
- Route organization
- Endpoint grouping
"""

# Version 1 routers
from app.router.v1 import (
    v1_router,
    mobile_router,
    church_router,
    admin_router,
    shared_router
)

# Main exports
__all__ = [
    # Version 1 routers
    "v1_router",
    "mobile_router",
    "church_router",
    "admin_router",
    "shared_router"
]
