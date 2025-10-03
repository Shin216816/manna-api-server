from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controller.shared.health import (
    health_check, detailed_health_check
)
from app.utils.database import get_db
from app.core.responses import SuccessResponse

health_router = APIRouter(tags=["System"])

@health_router.get("/health", response_model=SuccessResponse)
async def health_check_route():
    """
    Health check
    
    Basic health check endpoint that returns the API status.
    Used by load balancers and monitoring systems.
    """
    return health_check()

@health_router.get("/health/detailed", response_model=SuccessResponse)
async def detailed_health_check_route(
    db: Session = Depends(get_db)
):
    """
    Detailed health check
    
    Comprehensive health check including database connectivity,
    external services, and system status.
    """
    return detailed_health_check(db)
