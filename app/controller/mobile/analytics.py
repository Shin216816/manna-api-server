"""
Mobile Analytics Controller

Handles analytics for mobile app:
- User analytics
- Donation analytics
- Impact metrics
"""

from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.core.responses import ResponseFactory
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional


def get_user_analytics(user_id: int, db: Session):
    """Get user analytics data for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get donation statistics
        total_donations = db.query(func.count(DonationBatch.id)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).scalar() or 0
        
        total_amount = db.query(func.sum(DonationBatch.total_amount)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).scalar() or 0.0
        
        # Get this month's donations
        this_month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success",
                DonationBatch.executed_at >= this_month_start
            )
        ).scalar() or 0.0
        
        # Get roundup statistics
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user_id).first()
        roundup_enabled = preferences.is_active if preferences else False
        roundup_multiplier = preferences.multiplier if preferences else "1x"
        
        analytics_data = {
            "user_id": user_id,
            "total_donations": total_donations,
            "total_amount": float(total_amount),
            "this_month_amount": float(this_month_donations),
            "average_per_donation": float(total_amount / total_donations) if total_donations > 0 else 0.0,
            "roundup_enabled": roundup_enabled,
            "roundup_multiplier": roundup_multiplier,
            "member_since": user.created_at.isoformat() if user.created_at else None,
            "last_donation_date": None  # Will be populated if there are donations
        }
        
        # Get last donation date
        last_donation = db.query(DonationBatch).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).order_by(desc(DonationBatch.executed_at)).first()
        
        if last_donation and last_donation.executed_at:
            analytics_data["last_donation_date"] = last_donation.executed_at.isoformat()
        
        return ResponseFactory.success(
            message="User analytics retrieved successfully",
            data=analytics_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve user analytics")


def get_donation_analytics(user_id: int, db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get donation analytics for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build date filters
        date_filters = [DonationBatch.user_id == user_id, DonationBatch.status == "success"]
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filters.append(DonationBatch.executed_at >= start_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_filters.append(DonationBatch.executed_at <= end_datetime)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
        
        # Get donation data
        donations = db.query(DonationBatch).filter(and_(*date_filters)).order_by(desc(DonationBatch.executed_at)).all()
        
        total_amount = sum(donation.total_amount for donation in donations)
        total_donations = len(donations)
        
        # Group by month for trend analysis
        monthly_data = {}
        for donation in donations:
            if donation.executed_at:
                month_key = donation.executed_at.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {"amount": 0.0, "count": 0}
                monthly_data[month_key]["amount"] += donation.total_amount
                monthly_data[month_key]["count"] += 1
        
        # Convert to sorted list
        monthly_trends = [
            {
                "month": month,
                "amount": data["amount"],
                "count": data["count"]
            }
            for month, data in sorted(monthly_data.items(), reverse=True)
        ]
        
        analytics_data = {
            "user_id": user_id,
            "total_amount": float(total_amount),
            "total_donations": total_donations,
            "average_per_donation": float(total_amount / total_donations) if total_donations > 0 else 0.0,
            "monthly_trends": monthly_trends,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
        return ResponseFactory.success(
            message="Donation analytics retrieved successfully",
            data=analytics_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve donation analytics")


def get_impact_metrics(user_id: int, db: Session):
    """Get impact metrics for mobile app"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get total donations
        total_amount = db.query(func.sum(DonationBatch.total_amount)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "success"
            )
        ).scalar() or 0.0
        
        # Calculate impact metrics (example calculations)
        # These would typically come from church-provided data
        meals_provided = int(total_amount / 5.0)  # Assuming $5 per meal
        students_helped = int(total_amount / 100.0)  # Assuming $100 per student
        medical_visits = int(total_amount / 50.0)  # Assuming $50 per visit
        
        impact_data = {
            "user_id": user_id,
            "total_donated": float(total_amount),
            "impact_metrics": {
                "meals_provided": meals_provided,
                "students_helped": students_helped,
                "medical_visits": medical_visits,
                "families_supported": int(total_amount / 200.0),  # Assuming $200 per family
                "community_projects": int(total_amount / 500.0)  # Assuming $500 per project
            },
            "donation_breakdown": {
                "roundups": float(total_amount * 0.7),  # Assuming 70% from roundups
                "direct_donations": float(total_amount * 0.3)  # Assuming 30% direct
            }
        }
        
        return ResponseFactory.success(
            message="Impact metrics retrieved successfully",
            data=impact_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve impact metrics")
