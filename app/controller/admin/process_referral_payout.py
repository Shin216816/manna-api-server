from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.model.m_church_referral import ChurchReferral
from app.model.m_church import Church
from app.services.stripe_service import transfer_to_church
from app.utils.audit import create_audit_log
from app.schema.admin_schema import ReferralPayoutRequest
from app.core.responses import ResponseFactory
import uuid
import logging
from datetime import datetime, timezone

def process_referral_payout(referral_id: int, data: ReferralPayoutRequest, current_admin: dict, db: Session):
    """Process referral payout with real Stripe transfer"""
    try:
        # Get the referral record
        referral = db.query(ChurchReferral).filter_by(id=referral_id).first()
        if not referral:
            raise HTTPException(status_code=404, detail="Referral not found")
        
        if referral.commission_paid:
            raise HTTPException(status_code=400, detail="Commission already paid")

        # Get the referring church
        referrer_church = db.query(Church).filter_by(id=referral.referrer_id).first()
        if not referrer_church:
            raise HTTPException(status_code=400, detail="Referring church not found")
        
        # Check if church has Stripe account for transfers
        if not referrer_church.stripe_account_id:
            raise HTTPException(
                status_code=400, 
                detail="Church does not have a connected Stripe account for payouts"
            )
        
        # Calculate commission amount
        commission_amount = referral.commission_amount
        if commission_amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid commission amount")
        
        # Process real Stripe transfer
        try:
            transfer = transfer_to_church(
                amount_cents=int(commission_amount * 100),  # Convert to cents
                destination_account_id=referrer_church.stripe_account_id,
                metadata={
                    "referral_id": referral.id,
                    "type": "commission",
                    "referrer_church_id": referrer_church.id,
                    "referred_church_id": referral.referred_id,
                    "processed_by_admin_id": current_admin.get("admin_id", 0)
                }
            )
            
            # Update referral record with transfer details
            referral.commission_paid = True
            referral.payout_date = datetime.now(timezone.utc)
            referral.stripe_transfer_id = transfer.id
            referral.payout_amount = commission_amount
            
            db.commit()
            
            
            
            # Create audit log
            create_audit_log(
                db=db,
                actor_type="admin",
                actor_id=current_admin.get("admin_id", 0),
                action="referral_payout",
                metadata={
                    "resource_type": "referral",
                    "resource_id": referral.id,
                    "referral_id": referral.id,
                    "transfer_id": transfer.id,
                    "amount": commission_amount,
                    "church_id": referrer_church.id,
                    "church_name": referrer_church.name
                }
            )
            
            return ResponseFactory.success(
                message="Referral payout processed successfully",
                data={
                    "referral_id": referral.id,
                    "transfer_id": transfer.id,
                    "amount": commission_amount,
                    "church_name": referrer_church.name,
                    "payout_date": referral.payout_date.isoformat() if referral.payout_date else None
                }
            )
            
        except Exception as stripe_error:
            
            raise HTTPException(
                status_code=502, 
                detail=f"Stripe transfer failed: {str(stripe_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to process referral payout")
