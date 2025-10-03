from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.responses import BaseResponse, SuccessResponse, ErrorResponse

# ============================
# Webhook Schemas
# ============================

class WebhookEvent(BaseModel):
    """
    Base webhook event model for Stripe and Plaid webhooks.
    """
    event_type: str = Field(..., description="Type of webhook event")
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data payload")

class PlaidWebhookEvent(WebhookEvent):
    """Plaid webhook event"""
    webhook_type: str = Field(..., description="Plaid webhook type")
    webhook_code: str = Field(..., description="Plaid webhook code")

class StripeWebhookEvent(WebhookEvent):
    """Stripe webhook event"""
    stripe_event_id: str = Field(..., description="Stripe event ID")

class WebhookResponse(SuccessResponse):
    """Webhook processing response"""
    data: Optional[Dict[str, Any]] = None  # Contains processing result
