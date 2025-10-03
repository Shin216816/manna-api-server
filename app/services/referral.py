"""
Referral Service

Handles referral tracking and commission calculations for churches.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import logging

from app.model.m_church_referral import ChurchReferral
from app.model.m_donation_batch import DonationBatch
from app.model.m_church import Church
from app.config import config


def get_referral_summary(church_id: int, db: Session) -> List[Dict[str, Any]]:
    """Get referral summary for a church"""
    try:
        # Get all referrals for this church
        referrals = db.query(ChurchReferral).filter_by(referring_church_id=church_id).all()
        
        referral_data = []
        for referral in referrals:
            # Get referred church info
            referred_church = db.query(Church).filter_by(id=referral.referred_church_id).first()
            if not referred_church:
                continue
            
            # Calculate total donations from referred church
            total_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.church_id == referral.referred_church_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).scalar() or 0.0
            
            # Calculate commission earned
            commission_earned = total_donations * referral.commission_rate
            
            referral_data.append({
                "referral_id": referral.id,
                "referred_church_id": referral.referred_church_id,
                "church_name": referred_church.name,
                "referral_code": referral.referral_code,
                "commission_rate": referral.commission_rate,
                "commission_earned": round(commission_earned, 2),
                "total_generated": round(total_donations, 2),
                "date": referral.created_at.isoformat() if referral.created_at else None,
                "status": config.STATUS_SUCCESS
            })
        
        return referral_data
        
    except Exception as e:
        
        return []


def calculate_referral_commission(church_id: int, donation_amount: float, db: Session) -> float:
    """Calculate referral commission for a donation"""
    try:
        # Get the referral record
        referral = db.query(ChurchReferral).filter_by(referred_church_id=church_id).first()
        if not referral:
            return 0.0
        
        # Calculate commission
        commission = donation_amount * referral.commission_rate
        return round(commission, 2)
        
    except Exception as e:
        
        return 0.0


def track_referral_donation(referring_church_id: int, referred_church_id: int, donation_amount: float, db: Session) -> bool:
    """Track a donation that resulted from a referral"""
    try:
        # Get or create referral record
        referral = db.query(ChurchReferral).filter_by(
            referring_church_id=referring_church_id,
            referred_church_id=referred_church_id
        ).first()
        
        if not referral:
            # Create new referral record
            referral = ChurchReferral(
                referring_church_id=referring_church_id,
                referred_church_id=referred_church_id,
                commission_rate=config.REFERRAL_COMMISSION_RATE,
                status=config.STATUS_SUCCESS
            )
            db.add(referral)
            db.commit()
        
        # Update referral stats
        referral.total_donations = (referral.total_donations or 0) + donation_amount
        referral.commission_earned = (referral.commission_earned or 0) + (donation_amount * referral.commission_rate)
        referral.last_donation_date = datetime.now(timezone.utc)
        
        db.commit()
        return True
        
    except Exception as e:
        
        db.rollback()
        return False


def get_referral_stats(church_id: int, db: Session) -> Dict[str, Any]:
    """Get comprehensive referral statistics for a church"""
    try:
        # Get all referrals
        referrals = db.query(ChurchReferral).filter_by(referring_church_id=church_id).all()
        
        total_referrals = len(referrals)
        total_commission_earned = sum(r.commission_earned or 0 for r in referrals)
        total_donations_generated = sum(r.total_donations or 0 for r in referrals)
        
        # Get recent activity (last 30 days)
        last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
        recent_referrals = db.query(ChurchReferral).filter(
            and_(
                ChurchReferral.referring_church_id == church_id,
                ChurchReferral.last_donation_date >= last_30_days
            )
        ).count()
        
        return {
            "total_referrals": total_referrals,
            "total_commission_earned": round(total_commission_earned, 2),
            "total_donations_generated": round(total_donations_generated, 2),
            "recent_referrals": recent_referrals,
            "average_commission_rate": config.REFERRAL_COMMISSION_RATE,
            "status": config.STATUS_SUCCESS
        }
        
    except Exception as e:
        
        return {
            "total_referrals": 0,
            "total_commission_earned": 0.0,
            "total_donations_generated": 0.0,
            "recent_referrals": 0,
            "average_commission_rate": config.REFERRAL_COMMISSION_RATE,
            "status": config.STATUS_SUCCESS
        }
