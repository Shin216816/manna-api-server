from fastapi import APIRouter
from app.controller.shared.stripe import (
    create_payment_intent, confirm_payment, get_payment_status
)
from app.schema.stripe_schema import PaymentIntentCreateRequest, PaymentIntentConfirmRequest
from app.core.responses import SuccessResponse

stripe_router = APIRouter(tags=["Stripe Payments"])

@stripe_router.post("/payment-intent", response_model=SuccessResponse)
async def create_payment_intent_route(
    data: PaymentIntentCreateRequest
):
    """Create payment intent"""
    return create_payment_intent(data.amount, data.currency, data.metadata)

@stripe_router.post("/confirm", response_model=SuccessResponse)
async def confirm_payment_route(
    data: PaymentIntentConfirmRequest
):
    """Confirm payment"""
    return confirm_payment(data.payment_intent_id)

@stripe_router.get("/payment/{payment_id}", response_model=SuccessResponse)
async def get_payment_status_route(
    payment_id: str
):
    """Get payment status"""
    return get_payment_status(payment_id)
