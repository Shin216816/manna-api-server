"""
Stripe Payment Schemas

Defines request and response schemas for Stripe payment endpoints:
- Payment processing
- Webhook handling
- Payment method management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal


class CustomerCreateRequest(BaseModel):
    email: str = Field(..., description="Customer email address")
    name: Optional[str] = Field(None, description="Customer full name")
    phone: Optional[str] = Field(None, description="Customer phone number")


class CustomerUpdateRequest(BaseModel):
    email: Optional[str] = Field(None, description="Customer email address")
    name: Optional[str] = Field(None, description="Customer full name")
    phone: Optional[str] = Field(None, description="Customer phone number")
    address: Optional[Dict[str, Any]] = Field(None, description="Customer address")
    shipping: Optional[Dict[str, Any]] = Field(None, description="Customer shipping information")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")


class PaymentIntentCreateRequest(BaseModel):
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    description: Optional[str] = Field(None, description="Payment description")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")
    automatic_payment_methods: bool = Field(default=True, description="Enable automatic payment methods")
    church_id: Optional[int] = Field(None, description="Church ID for donation")
    donation_type: Optional[str] = Field(default="one_time", description="Type of donation")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['usd', 'eur', 'gbp', 'cad', 'aud']
        if v.lower() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.lower()


class PaymentIntentConfirmRequest(BaseModel):
    payment_intent_id: str = Field(..., description="Payment Intent ID")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    return_url: Optional[str] = Field(None, description="Return URL for redirect flows")


class SetupIntentCreateRequest(BaseModel):
    customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    payment_method_types: Optional[List[str]] = Field(
        default=["card"], 
        description="List of payment method types"
    )
    usage: str = Field(default="off_session", description="Setup intent usage")

    @validator('usage')
    def validate_usage(cls, v):
        valid_usage = ['off_session', 'on_session']
        if v not in valid_usage:
            raise ValueError(f'Usage must be one of: {valid_usage}')
        return v


class PaymentMethodAttachRequest(BaseModel):
    payment_method_id: str = Field(..., description="Payment method ID to attach")


class PaymentMethodUpdateRequest(BaseModel):
    billing_details: Optional[Dict[str, Any]] = Field(None, description="Billing details")
    card: Optional[Dict[str, Any]] = Field(None, description="Card details")


class ChargeCreateRequest(BaseModel):
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")
    description: Optional[str] = Field(None, description="Charge description")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")
    church_id: Optional[int] = Field(None, description="Church ID for donation")
    donation_type: Optional[str] = Field(default="one_time", description="Type of donation")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class ConnectAccountCreateRequest(BaseModel):
    type: str = Field(default="express", description="Account type")
    country: str = Field(default="US", description="Country code")
    email: Optional[str] = Field(None, description="Account email")
    business_type: Optional[str] = Field(None, description="Business type")

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['express', 'standard', 'custom']
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {valid_types}')
        return v


class AccountLinkCreateRequest(BaseModel):
    refresh_url: str = Field(..., description="Refresh URL")
    return_url: str = Field(..., description="Return URL")
    type: str = Field(default="account_onboarding", description="Link type")

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['account_onboarding', 'account_update']
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {valid_types}')
        return v


class RefundCreateRequest(BaseModel):
    charge_id: str = Field(..., description="Charge ID to refund")
    amount: Optional[int] = Field(None, description="Refund amount in cents")
    reason: Optional[str] = Field(None, description="Refund reason")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")

    @validator('reason')
    def validate_reason(cls, v):
        if v:
            valid_reasons = ['duplicate', 'fraudulent', 'requested_by_customer']
            if v not in valid_reasons:
                raise ValueError(f'Reason must be one of: {valid_reasons}')
        return v


class TransferCreateRequest(BaseModel):
    amount_cents: int = Field(..., description="Transfer amount in cents")
    church_id: int = Field(..., description="Church ID")
    description: Optional[str] = Field(None, description="Transfer description")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")

    @validator('amount_cents')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


# Response schemas
class StripeCustomerResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    phone: Optional[str]
    created: int
    metadata: Dict[str, str]


class StripePaymentIntentResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    client_secret: str
    customer: Optional[str]
    payment_method: Optional[str]
    description: Optional[str]
    metadata: Dict[str, str]
    created: int


class StripeSetupIntentResponse(BaseModel):
    id: str
    status: str
    client_secret: str
    customer: Optional[str]
    payment_method_types: List[str]
    usage: str
    created: int


class StripePaymentMethodResponse(BaseModel):
    id: str
    type: str
    card: Optional[Dict[str, Any]]
    billing_details: Optional[Dict[str, Any]]
    customer: Optional[str]
    created: int


class StripeChargeResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    customer: Optional[str]
    payment_method: Optional[str]
    description: Optional[str]
    metadata: Dict[str, str]
    created: int


class StripeConnectAccountResponse(BaseModel):
    id: str
    type: str
    country: str
    email: Optional[str]
    business_type: Optional[str]
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    created: int


class StripeAccountLinkResponse(BaseModel):
    url: str
    created: int
    expires_at: int


class StripeRefundResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    charge: str
    reason: Optional[str]
    metadata: Dict[str, str]
    created: int


class StripeTransferResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    destination: str
    description: Optional[str]
    metadata: Dict[str, str]
    created: int


class StripeBalanceResponse(BaseModel):
    available: List[Dict[str, Any]]
    pending: List[Dict[str, Any]]
    instant_available: List[Dict[str, Any]]


# Webhook event schemas
class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    created: int
    livemode: bool
    pending_webhooks: int
    request: Optional[Dict[str, Any]]


class StripeWebhookRequest(BaseModel):
    event: StripeWebhookEvent
    signature: str
    timestamp: int


# Error response schemas
class StripeErrorResponse(BaseModel):
    error: str
    error_type: str
    error_code: Optional[str]
    error_message: str
    request_id: Optional[str]


# Success response schemas
class StripeSuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None 
