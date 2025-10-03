"""
Church Referral Controller

Handles church referral functionality:
- Generate unique referral codes
- Track referrals and commissions
- Manage referral payouts
"""

import logging
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.model.m_church import Church
from app.model.m_church_referral import ChurchReferral
from app.model.m_referral import ReferralCommission
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.core.responses import ResponseFactory
from app.core.exceptions import ValidationError, NotFoundError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException


@handle_controller_errors
def generate_referral_code(church_id: int, db: Session) -> ResponseFactory:
    """Generate a unique referral code for a church"""
    try:
        # Verify church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        
        # Check if church already has an active referral code
        existing_referral = db.query(ChurchReferral).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active"
        ).first()

        if existing_referral:
            return ResponseFactory.success(
                message="Referral code already exists",
                data={
                    "referral_code": existing_referral.referral_code,
                    "created_at": existing_referral.created_at.isoformat(),
                    "expires_at": existing_referral.expires_at.isoformat() if existing_referral.expires_at else None
                }
            )

        # Generate unique referral code
        referral_code = f"MANNA-{church_id:04d}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create referral record
        referral = ChurchReferral(
            referring_church_id=church_id,
            referred_church_id=None,  # Will be set when someone uses the code
            referral_code=referral_code,
            status="active",
            commission_rate=0.05,  # 5% commission
            expires_at=datetime.now(timezone.utc) + timedelta(days=365)  # 1 year validity
        )
        
        db.add(referral)
        db.commit()
        db.refresh(referral)

        return ResponseFactory.success(
            message="Referral code generated successfully",
            data={
                "referral_code": referral_code,
                "created_at": referral.created_at.isoformat(),
                "expires_at": referral.expires_at.isoformat(),
                "commission_rate": referral.commission_rate
            }
        )

    except Exception as e:
        logging.error(f"Error generating referral code: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to generate referral code")


@handle_controller_errors
def get_referral_info(church_id: int, db: Session) -> ResponseFactory:
    """Get church's referral information and statistics"""
    try:
        # Verify church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        
        # Get active referral code
        referral = db.query(ChurchReferral).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active"
        ).first()

        if not referral:
            return ResponseFactory.success(
                message="No active referral code found",
                data={
                    "has_referral_code": False,
                    "referral_code": None,
                    "total_referrals": 0,
                    "total_commission_earned": 0.0,
                    "pending_commission": 0.0
                }
            )

        # Get referral statistics - count actual referrals (where referred_church_id is not null)
        total_referrals = db.query(func.count(ChurchReferral.id)).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active",
            ChurchReferral.referred_church_id.isnot(None)
        ).scalar()

        # Get total commission earned
        total_commission = db.query(func.sum(ReferralCommission.amount)).filter(
            ReferralCommission.referring_church_id == church_id
        ).scalar() or 0.0

        # Get pending commission (assume all commissions are paid for now since we don't have status field)
        pending_commission = 0.0

        # Get recent referrals - only actual referrals where referred_church_id is not null
        recent_referrals = db.query(ChurchReferral).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active",
            ChurchReferral.referred_church_id.isnot(None)
        ).order_by(desc(ChurchReferral.created_at)).limit(10).all()

        referrals_data = []
        for ref in recent_referrals:
            referred_church = db.query(Church).filter(Church.id == ref.referred_church_id).first()
            referrals_data.append({
                "id": ref.id,
                "name": referred_church.name if referred_church else "Unknown",
                "joined_at": ref.created_at.isoformat(),
                "commission_earned": ref.total_commission_earned
            })

        return ResponseFactory.success(
            message="Referral information retrieved successfully",
            data={
                "has_referral_code": True,
                "referral_code": referral.referral_code,
                "created_at": referral.created_at.isoformat(),
                "expires_at": referral.expires_at.isoformat() if referral.expires_at else None,
                "commission_rate": referral.commission_rate,
                "total_referrals": total_referrals,
                "total_commission_earned": float(total_commission),
                "pending_commission": float(pending_commission),
                "recent_referrals": referrals_data
            }
        )

    except Exception as e:
        logging.error(f"Error getting referral info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get referral information")


@handle_controller_errors
def use_referral_code(referral_code: str, church_id: int, db: Session) -> ResponseFactory:
    """Use a referral code when a new church registers"""
    try:
        # Find the referral code
        referral = db.query(ChurchReferral).filter(
            ChurchReferral.referral_code == referral_code,
            ChurchReferral.status == "active"
        ).first()

        if not referral:
            raise ValidationError("Invalid or expired referral code")

        # Check if referral code is expired
        if referral.expires_at and referral.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Referral code has expired")

        # Check if church is trying to use their own referral code
        if referral.referring_church_id == church_id:
            raise ValidationError("Cannot use your own referral code")

        # Update the referral record
        referral.referred_church_id = church_id
        referral.updated_at = datetime.now(timezone.utc)
        
        db.commit()

        # Get referring church info
        referring_church = db.query(Church).filter(Church.id == referral.referring_church_id).first()

        return ResponseFactory.success(
            message="Referral code used successfully",
            data={
                "referring_church_name": referring_church.name if referring_church else "Unknown",
                "commission_rate": referral.commission_rate,
                "referral_code": referral_code
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error using referral code: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to use referral code")


@handle_controller_errors
def validate_referral_code(referral_code: str, db: Session) -> ResponseFactory:
    """Validate a referral code without using it"""
    try:
        # Find the referral code
        referral = db.query(ChurchReferral).filter(
            ChurchReferral.referral_code == referral_code,
            ChurchReferral.status == "active"
        ).first()

        if not referral:
            return ResponseFactory.error(
                message="Invalid or inactive referral code",
                error_code="INVALID_REFERRAL_CODE"
            )

        # Check if referral code is expired
        if referral.expires_at and referral.expires_at < datetime.now(timezone.utc):
            return ResponseFactory.error(
                message="Referral code has expired",
                error_code="EXPIRED_REFERRAL_CODE"
            )

        # Get referring church info
        referring_church = db.query(Church).filter(Church.id == referral.referring_church_id).first()

        return ResponseFactory.success(
            message="Referral code is valid",
            data={
                "valid": True,
                "referring_church_name": referring_church.name if referring_church else "Unknown",
                "commission_rate": referral.commission_rate,
                "expires_at": referral.expires_at.isoformat() if referral.expires_at else None
            }
        )

    except Exception as e:
        logging.error(f"Error validating referral code: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate referral code")


@handle_controller_errors
def calculate_referral_commissions(church_id: int, db: Session) -> ResponseFactory:
    """Calculate and record referral commissions for a church"""
    try:
        # Get all active referrals for this church
        referrals = db.query(ChurchReferral).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active"
        ).all()

        total_commission = 0.0
        commissions_created = 0

        for referral in referrals:
            # Skip if no referred church or self-referral
            if not referral.referred_church_id or referral.referred_church_id == referral.referring_church_id:
                continue

            # Get revenue from referred church in the last month
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Get church payouts from referred church
            church_payouts = db.query(ChurchPayout).filter(
                ChurchPayout.church_id == referral.referred_church_id,
                ChurchPayout.status == "completed",
                ChurchPayout.created_at >= start_date
            ).all()

            # Process each payout individually to avoid duplicates
            for payout in church_payouts:
                # Calculate commission for this specific payout
                commission_amount = float(payout.net_payout_amount) * referral.commission_rate
                
                if commission_amount > 0:
                    # Check if commission already exists for this specific payout
                    existing_commission = db.query(ReferralCommission).filter(
                        ReferralCommission.referring_church_id == referral.referring_church_id,
                        ReferralCommission.referred_church_id == referral.referred_church_id,
                        ReferralCommission.description.like(f"%payout_id_{payout.id}%")
                    ).first()

                    if not existing_commission:
                        # Create commission record for this specific payout
                        commission = ReferralCommission(
                            referring_church_id=referral.referring_church_id,
                            referred_church_id=referral.referred_church_id,
                            amount=commission_amount,
                            commission_rate=referral.commission_rate,
                            description=f"Commission for payout_id_{payout.id} on {payout.created_at.strftime('%Y-%m-%d')} - ${commission_amount:.2f}"
                        )
                        
                        db.add(commission)
                        total_commission += commission_amount
                        commissions_created += 1
                        
                        # Update referral record with total commission earned
                        referral.total_commission_earned = (referral.total_commission_earned or 0) + commission_amount

        db.commit()

        return ResponseFactory.success(
            message="Referral commissions calculated successfully",
            data={
                "commissions_created": commissions_created,
                "total_commission": float(total_commission)
            }
        )

    except Exception as e:
        logging.error(f"Error calculating referral commissions: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to calculate referral commissions")


@handle_controller_errors
def get_referral_commissions(church_id: int, page: int = 1, limit: int = 20, db: Session = None) -> ResponseFactory:
    """Get referral commission history for a church"""
    try:
        offset = (page - 1) * limit

        # Get commissions where the church is the referring church (earning commissions)
        commissions = db.query(ReferralCommission).filter(
            ReferralCommission.referring_church_id == church_id
        ).order_by(desc(ReferralCommission.created_at)).offset(offset).limit(limit).all()

        total_count = db.query(func.count(ReferralCommission.id)).filter(
            ReferralCommission.referring_church_id == church_id
        ).scalar()

        commissions_data = []
        for commission in commissions:
            # Get referred church info
            referred_church = db.query(Church).filter(Church.id == commission.referred_church_id).first()

            commissions_data.append({
                "id": commission.id,
                "amount": float(commission.amount),
                "commission_rate": float(commission.commission_rate),
                "description": commission.description,
                "created_at": commission.created_at.isoformat(),
                "updated_at": commission.updated_at.isoformat(),
                "referred_church_name": referred_church.name if referred_church else "Unknown",
                "referred_church_id": commission.referred_church_id
            })

        return ResponseFactory.success(
            message="Referral commissions retrieved successfully",
            data={
                "commissions": commissions_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit
                }
            }
        )

    except Exception as e:
        logging.error(f"Error getting referral commissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get referral commissions")


@handle_controller_errors
def process_commission_payouts(church_id: int, db: Session) -> ResponseFactory:
    """Process pending commission payouts for a church"""
    try:
        # Get church information
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get all commissions for this church (referring church earning commissions)
        commissions = db.query(ReferralCommission).filter(
            ReferralCommission.referring_church_id == church_id
        ).all()

        if not commissions:
            return ResponseFactory.success(
                message="No commissions found to process",
                data={
                    "processed_count": 0,
                    "total_amount": 0.0
                }
            )

        # Calculate total commission amount
        total_amount = sum(commission.amount for commission in commissions)
        
        # Create a single payout record for all commissions
        # This would integrate with the existing payout system
        payout_record = {
            "church_id": church_id,
            "amount": total_amount,
            "type": "referral_commission",
            "description": f"Referral commission payout for {len(commissions)} commissions",
            "status": "pending",
            "created_at": datetime.now(timezone.utc)
        }

        # In a real implementation, this would create a ChurchPayout record
        # For now, we'll just log the payout information
        logging.info(f"Processing referral commission payout for church {church_id}: ${total_amount:.2f}")

        # Update referral records to mark last payout
        referral_records = db.query(ChurchReferral).filter(
            ChurchReferral.referring_church_id == church_id
        ).all()

        for referral in referral_records:
            referral.last_commission_payout = datetime.now(timezone.utc)

        db.commit()

        return ResponseFactory.success(
            message="Commission payouts processed successfully",
            data={
                "processed_count": len(commissions),
                "total_amount": float(total_amount),
                "payout_date": datetime.now(timezone.utc).isoformat(),
                "church_name": church.name
            }
        )

    except Exception as e:
        logging.error(f"Error processing commission payouts: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process commission payouts")


@handle_controller_errors
def get_referral_analytics(church_id: int, days: int = 30, db: Session = None) -> ResponseFactory:
    """Get detailed referral analytics for a church"""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get referral statistics
        total_referrals = db.query(func.count(ChurchReferral.id)).filter(
            ChurchReferral.referring_church_id == church_id,
            ChurchReferral.status == "active",
            ChurchReferral.created_at >= start_date
        ).scalar()

        # Get commission statistics
        total_commission = db.query(func.sum(ReferralCommission.amount)).filter(
            ReferralCommission.referring_church_id == church_id,
            ReferralCommission.created_at >= start_date
        ).scalar() or 0.0

        # Since we don't have status field, assume all commissions are paid
        paid_commission = total_commission
        pending_commission = 0.0

        # Get monthly breakdown
        monthly_data = []
        for i in range(days // 7):  # Weekly breakdown
            week_start = start_date + timedelta(days=i * 7)
            week_end = min(week_start + timedelta(days=7), end_date)
            
            week_referrals = db.query(func.count(ChurchReferral.id)).filter(
                ChurchReferral.referring_church_id == church_id,
                ChurchReferral.status == "active",
                ChurchReferral.created_at >= week_start,
                ChurchReferral.created_at < week_end
            ).scalar()

            week_commission = db.query(func.sum(ReferralCommission.amount)).filter(
                ReferralCommission.referring_church_id == church_id,
                ReferralCommission.created_at >= week_start,
                ReferralCommission.created_at < week_end
            ).scalar() or 0.0

            monthly_data.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "referrals": week_referrals,
                "commission": float(week_commission)
            })

        # Get top performing referrals
        top_referrals = db.query(
            ReferralCommission.referred_church_id,
            func.sum(ReferralCommission.amount).label('total_commission'),
            func.count(ReferralCommission.id).label('commission_count')
        ).filter(
            ReferralCommission.referring_church_id == church_id,
            ReferralCommission.created_at >= start_date
        ).group_by(ReferralCommission.referred_church_id).order_by(
            func.sum(ReferralCommission.amount).desc()
        ).limit(5).all()

        top_referrals_data = []
        for ref in top_referrals:
            referred_church = db.query(Church).filter(Church.id == ref.referred_church_id).first()
            top_referrals_data.append({
                "church_name": referred_church.name if referred_church else "Unknown",
                "total_commission": float(ref.total_commission),
                "commission_count": ref.commission_count
            })

        return ResponseFactory.success(
            message="Referral analytics retrieved successfully",
            data={
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "summary": {
                    "total_referrals": total_referrals,
                    "total_commission": float(total_commission),
                    "paid_commission": float(paid_commission),
                    "pending_commission": float(pending_commission)
                },
                "monthly_breakdown": monthly_data,
                "top_referrals": top_referrals_data
            }
        )

    except Exception as e:
        logging.error(f"Error getting referral analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get referral analytics")


@handle_controller_errors
def validate_referral_code(referral_code: str, db: Session) -> ResponseFactory:
    """Validate a referral code without using it"""
    try:
        # Find the referral code
        referral = db.query(ChurchReferral).filter(
            ChurchReferral.referral_code == referral_code,
            ChurchReferral.status == "active"
        ).first()

        if not referral:
            return ResponseFactory.error(
                message="Invalid referral code",
                data={"valid": False, "reason": "not_found"}
            )

        # Check if referral code is expired
        if referral.expires_at and referral.expires_at < datetime.now(timezone.utc):
            return ResponseFactory.error(
                message="Referral code has expired",
                data={"valid": False, "reason": "expired"}
            )

        # Get referring church info
        referring_church = db.query(Church).filter(Church.id == referral.referring_church_id).first()

        return ResponseFactory.success(
            message="Referral code is valid",
            data={
                "valid": True,
                "referring_church_name": referring_church.name if referring_church else "Unknown",
                "commission_rate": referral.commission_rate,
                "expires_at": referral.expires_at.isoformat() if referral.expires_at else None
            }
        )

    except Exception as e:
        logging.error(f"Error validating referral code: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate referral code")