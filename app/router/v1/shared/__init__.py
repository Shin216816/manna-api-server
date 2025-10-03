"""
Shared Router for Common Functionality

Handles shared endpoints used across different user types:
- Health checks and monitoring
- File uploads and media management
- Webhook handlers
- Stripe payment processing
- Common utilities and services
"""

from fastapi import APIRouter

# Import shared sub-routers
from app.router.v1.shared.health import health_router
from app.router.v1.shared.webhooks import webhook_router
from app.router.v1.shared.stripe import stripe_router
from app.router.v1.shared.files import files_router
from app.router.v1.shared.sessions import router as sessions_router

# Create main shared router
shared_router = APIRouter()

# Include all shared sub-routers
shared_router.include_router(health_router, tags=["Health & Monitoring"])
shared_router.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
shared_router.include_router(stripe_router, prefix="/stripe", tags=["Stripe Payments"])
shared_router.include_router(files_router, prefix="/files", tags=["File Management"])
shared_router.include_router(sessions_router, prefix="/sessions", tags=["Session Management"])

# Main exports
__all__ = [
    "shared_router",
    "health_router",
    "webhook_router",
    "stripe_router",
    "files_router",
    "sessions_router"
]
