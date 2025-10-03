from fastapi import APIRouter
from app.router.v1.public.churches import router as churches_router
from app.router.v1.public.contact import router as contact_router

public_router = APIRouter(tags=["Public"])

# Include public sub-routers
public_router.include_router(churches_router, prefix="/churches", tags=["Public Churches"])
public_router.include_router(contact_router, prefix="/contact", tags=["Public Contact"])
