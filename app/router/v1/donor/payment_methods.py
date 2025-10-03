from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.controller.donor.payment_methods import (
    add_card_payment_method,
    get_payment_methods_enhanced,
    set_default_payment_method_enhanced,
    remove_payment_method_enhanced,
    verify_payment_method_enhanced
)

router = APIRouter()

@router.post("/add")
def add_payment_method_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new payment method for a donor"""
    return add_card_payment_method(current_user, data, db)

@router.get("/list")
def get_payment_methods_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payment methods for a donor"""
    return get_payment_methods_enhanced(current_user, db)

@router.post("/set-default")
def set_default_payment_method_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a payment method as default"""
    return set_default_payment_method_enhanced(current_user, data, db)

@router.post("/remove")
def remove_payment_method_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a payment method"""
    return remove_payment_method_enhanced(current_user, data, db)

@router.post("/verify")
def verify_payment_method_route(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a payment method with a small test charge"""
    return verify_payment_method_enhanced(current_user, data, db)
