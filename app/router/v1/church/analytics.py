from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_church_admin_auth
from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
# RoundupTransaction removed - using DonationBatch data instead
from app.schema.analytics_schema import ChurchAnalyticsResponse, ChurchAnalyticsData
from typing import Optional
from datetime import datetime, timedelta
import calendar

router = APIRouter()

# Endpoint path should be root here; aggregator mounts under /church/analytics
@router.get("/", response_model=ChurchAnalyticsResponse)
async def get_church_analytics(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_admin: dict = Depends(jwt_church_admin_auth),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for the church"""
    try:
        church_id = current_admin.get("church_id")
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow().date()
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        # Get church data
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Church not found"
            )
        
        # Calculate total donations
        total_donations_query = db.query(func.sum(DonationBatch.amount)).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= start_date,
                DonationBatch.created_at <= end_date
            )
        )
        total_donations = total_donations_query.scalar() or 0.0
        
        # Calculate donation growth (compare with previous period)
        prev_start = start_date - (end_date - start_date)
        prev_end = start_date
        
        prev_donations_query = db.query(func.sum(DonationBatch.amount)).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= prev_start,
                DonationBatch.created_at <= prev_end
            )
        )
        prev_donations = prev_donations_query.scalar() or 0.0
        
        donation_growth = 0.0
        if prev_donations > 0:
            donation_growth = ((total_donations - prev_donations) / prev_donations) * 100
        
        # Get active givers count
        active_givers_query = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= start_date,
                DonationBatch.created_at <= end_date
            )
        )
        active_givers = active_givers_query.scalar() or 0
        
        # Calculate giver growth
        prev_givers_query = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= prev_start,
                DonationBatch.created_at <= prev_end
            )
        )
        prev_givers = prev_givers_query.scalar() or 0
        
        giver_growth = 0.0
        if prev_givers > 0:
            giver_growth = ((active_givers - prev_givers) / prev_givers) * 100
        
        # Calculate average donation
        avg_donation = 0.0
        if active_givers > 0:
            avg_donation = total_donations / active_givers
        
        # Get total transactions count
        total_transactions_query = db.query(func.count(DonationBatch.id)).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= start_date,
                DonationBatch.created_at <= end_date
            )
        )
        total_transactions = total_transactions_query.scalar() or 0
        
        # This month donations
        current_month_start = datetime.utcnow().replace(day=1).date()
        this_month_donations_query = db.query(func.sum(DonationBatch.amount)).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_month_start
            )
        )
        this_month_donations = this_month_donations_query.scalar() or 0.0
        
        # Monthly growth
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        
        last_month_donations_query = db.query(func.sum(DonationBatch.amount)).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= last_month_start,
                DonationBatch.created_at <= last_month_end
            )
        )
        last_month_donations = last_month_donations_query.scalar() or 0.0
        
        monthly_growth = 0.0
        if last_month_donations > 0:
            monthly_growth = ((this_month_donations - last_month_donations) / last_month_donations) * 100
        
        # Get donation trends (daily data for the period)
        donation_trends = []
        current_date = start_date
        while current_date <= end_date:
            daily_donations_query = db.query(func.sum(DonationBatch.amount)).filter(
                and_(
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                    func.date(DonationBatch.created_at) == current_date
                )
            )
            daily_donations = daily_donations_query.scalar() or 0.0
            
            donation_trends.append({
                "date": current_date.isoformat(),
                "amount": daily_donations
            })
            
            current_date += timedelta(days=1)
        
        # Get spending categories from Plaid transactions (simplified analytics)
        # Note: Detailed merchant analytics require real-time data from Plaid API
        # For now, we'll provide basic donation batch analytics
        spending_categories = []
        top_merchants = []
        
        # Basic analytics from DonationBatch data
        donation_batches = db.query(DonationBatch).filter(
            and_(
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= start_date,
                DonationBatch.created_at <= end_date
            )
        ).all()
        
        # Calculate basic metrics
        total_donations = sum(batch.amount for batch in donation_batches)
        total_transactions = sum(batch.transaction_count for batch in donation_batches)
        
        if total_donations > 0:
            spending_categories.append({
                "name": "Roundup Donations",
                "amount": total_donations,
                "percentage": 100.0,
                "transaction_count": total_transactions,
                "color": "#3B82F6"
            })
        
        # Top merchants would require real-time Plaid data
        # For now, show basic donation information
        if donation_batches:
            top_merchants.append({
                "name": "Roundup Donations",
                "amount": total_donations,
                "transaction_count": total_transactions
            })
        
        analytics_data = ChurchAnalyticsData(
            total_donations=total_donations,
            donation_growth=donation_growth,
            active_givers=active_givers,
            giver_growth=giver_growth,
            avg_donation=avg_donation,
            total_transactions=total_transactions,
            this_month_donations=this_month_donations,
            monthly_growth=monthly_growth,
            donation_trends=donation_trends,
            spending_categories=spending_categories,
            top_merchants=top_merchants
        )
        
        return ChurchAnalyticsResponse(
            success=True,
            data=analytics_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

def get_category_color(category: str) -> str:
    """Get color for spending category"""
    color_map = {
        "grocery": "#10B981",
        "gas": "#F59E0B", 
        "restaurant": "#EF4444",
        "retail": "#8B5CF6",
        "online": "#06B6D4",
        "other": "#6B7280"
    }
    return color_map.get(category, "#6B7280")