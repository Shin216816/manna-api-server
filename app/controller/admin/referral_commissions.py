from fastapi import HTTPException
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.model.m_church_referral import ChurchReferral
from app.model.m_church import Church
from sqlalchemy import func

from app.utils.audit import create_audit_log
from app.core.responses import ResponseFactory
from datetime import datetime, timezone


def list_referral_commissions(db):
    """List all referral commissions"""
    try:
        # Get all referral records
        referrals = db.query(ChurchReferral).all()
        
        data = []
        for referral in referrals:
            # Get church names
            referrer_church = db.query(Church).filter_by(id=referral.referring_church_id).first()
            referred_church = db.query(Church).filter_by(id=referral.referred_church_id).first()
            
            data.append({
                "referrer_id": referral.referring_church_id,
                "referred_id": referral.referred_church_id,
                "referral_code": referral.referral_code,
                "total_generated": float(referral.total_donations or 0),
                "commission": float(referral.total_commission_earned or 0),
                "paid": referral.commission_paid or False
            })

        return ResponseFactory.success(
            message="Referral commissions retrieved successfully",
            data=data
        )

    except SQLAlchemyError as db_err:
        
        raise HTTPException(status_code=500, detail="ADMIN.REFERRAL_COMMISSIONS.DB_ERROR")

    except Exception as e:
        
        raise HTTPException(status_code=500, detail="ADMIN.REFERRAL_COMMISSIONS.ERROR")


def mark_referral_commission_paid_controller(referrer_id: int, admin_id: int, db):
    """Mark referral commission as paid"""
    try:
        # Get all referrals for this referrer
        referrals = db.query(ChurchReferral).filter_by(referring_church_id=referrer_id).all()
        
        total_commission = 0.0
        for referral in referrals:
            if not referral.commission_paid:
                referral.commission_paid = True
                referral.payout_date = datetime.now(timezone.utc)
                total_commission += float(referral.total_commission_earned or 0)
        
        db.commit()

        create_audit_log(
            db=db,
            actor_type="platform_admin",
            actor_id=admin_id,
            action="referral_commission_paid",
            metadata={"referrer_id": referrer_id, "amount": total_commission}
        )

        return ResponseFactory.success(
            message="Referral commission marked as paid",
            data={
                "referrer_id": referrer_id,
                "total_commission": total_commission,
                "marked_paid": True
            }
        )

    except SQLAlchemyError as db_err:
        
        raise HTTPException(status_code=500, detail="ADMIN.REFERRAL_COMMISSION.DB_ERROR")

    except Exception as e:
        
        raise HTTPException(status_code=500, detail="ADMIN.REFERRAL_COMMISSION.ERROR")


def payout_commission(referral_id: int, admin_id: int, db):
    """Process referral commission payout using unified service"""
    try:
        from app.controller.admin.process_referral_payout import process_referral_payout
        from app.schema.admin_schema import ReferralPayoutRequest
        
        # Create a dummy data object since the function expects it
        data = ReferralPayoutRequest(church_id=0, amount=0.0, notes="Commission payout")
        current_admin = {"admin_id": admin_id}
        process_referral_payout(referral_id, data, current_admin, db)
        
        return ResponseFactory.success(
            message="Referral commission paid successfully",
            data={
                "referral_id": referral_id,
                "paid": True
            }
        )

    except SQLAlchemyError as db_err:
        
        raise HTTPException(status_code=500, detail="ADMIN.REFERRAL_COMMISSION.DB_ERROR")

    except Exception as e:
        
        raise HTTPException(status_code=500, detail="ADMIN.REFERRAL_COMMISSION.ERROR") 
