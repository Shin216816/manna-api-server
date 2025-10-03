from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.controller.shared.stripe_webhook import handle_stripe_webhook
from app.controller.shared.plaid_webhook import handle_plaid_webhook
from app.utils.database import get_db
from app.core.responses import SuccessResponse

webhook_router = APIRouter(tags=["Webhooks"])

@webhook_router.post("/stripe", response_model=SuccessResponse)
async def stripe_webhook_route(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        # Get the raw body
        body = await request.body()
        
        # Get the signature from headers
        signature = request.headers.get("stripe-signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        # Parse JSON payload
        import json
        payload = json.loads(body.decode('utf-8'))
        
        # Handle the webhook
        result = handle_stripe_webhook(payload, signature, db)
        
        return SuccessResponse(
            success=True,
            message="Webhook processed successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@webhook_router.post("/plaid", response_model=SuccessResponse)
async def plaid_webhook_route(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Plaid webhook events"""
    try:
        # Get the raw body
        body = await request.body()
        
        # Parse JSON payload
        import json
        payload = json.loads(body.decode('utf-8'))
        
        # Handle the webhook
        result = handle_plaid_webhook(payload, db)
        
        return SuccessResponse(
            success=True,
            message="Plaid webhook processed successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Plaid webhook processing failed")

@webhook_router.get("/health", response_model=SuccessResponse)
async def webhook_health_check():
    """Webhook health check"""
    from datetime import datetime
    return SuccessResponse(
        success=True,
        message="Webhook endpoints are healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "supported_events": [
                "payment_intent.succeeded",
                "payment_intent.payment_failed",
                "charge.succeeded",
                "charge.failed",
                "payout.paid",
                "payout.failed"
            ]
        }
    )
