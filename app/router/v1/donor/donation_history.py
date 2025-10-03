from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.utils.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.model.m_donation_batch import DonationBatch
# RoundupTransaction removed - using DonationBatch.transaction_count instead
from app.model.m_church import Church
from app.schema.donation_history_schema import DonationHistoryResponse, DonationHistoryData, DonationData
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()

# Endpoint path should be root here; aggregator mounts under /donor/donation-history
@router.get("/", response_model=DonationHistoryResponse)
async def get_donation_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get donor's donation history with filtering"""
    try:
        user_id = current_user.get("user_id")
        
        # Build query
        query = db.query(DonationBatch).filter(DonationBatch.user_id == user_id)
        
        # Apply filters
        if status:
            query = query.filter(DonationBatch.status == status)
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(DonationBatch.created_at >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(DonationBatch.created_at <= end_date_obj)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        donations = query.order_by(desc(DonationBatch.created_at)).offset(offset).limit(limit).all()
        
        # Format donation data
        donation_data = []
        for donation in donations:
            # Get church info
            church = db.query(Church).filter(Church.id == donation.church_id).first()
            
            # Get transaction count from DonationBatch (already stored)
            transaction_count = donation.transaction_count or 0
            
            donation_data.append(DonationData(
                id=donation.id,
                amount=donation.amount,
                status=donation.status,
                type=donation.type or "roundup",
                frequency=donation.frequency,
                multiplier=donation.multiplier,
                created_at=donation.created_at,
                collection_date=donation.collection_date,
                payout_date=donation.payout_date,
                church_name=church.name if church else "Unknown Church",
                transaction_count=transaction_count,
                processing_fees=float(donation.processing_fee) if donation.processing_fee else None
            ))
        
        # Calculate summary statistics
        total_amount = db.query(func.sum(DonationBatch.amount)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "completed"
            )
        ).scalar() or 0.0
        
        total_batches = db.query(func.count(DonationBatch.id)).filter(
            and_(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "completed"
            )
        ).scalar() or 0
        
        average_per_batch = total_amount / total_batches if total_batches > 0 else 0.0
        
        # Calculate impact score (simple calculation)
        impact_score = int(total_amount * 10)  # $1 = 10 impact points
        
        # Get monthly trends (last 12 months)
        monthly_trends = []
        for i in range(12):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)
            
            month_donations = db.query(func.sum(DonationBatch.amount)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == "completed",
                    DonationBatch.created_at >= month_start,
                    DonationBatch.created_at < month_end
                )
            ).scalar() or 0.0
            
            month_count = db.query(func.count(DonationBatch.id)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == "completed",
                    DonationBatch.created_at >= month_start,
                    DonationBatch.created_at < month_end
                )
            ).scalar() or 0
            
            # Calculate growth
            prev_month_start = month_start - timedelta(days=30)
            prev_month_donations = db.query(func.sum(DonationBatch.amount)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == "completed",
                    DonationBatch.created_at >= prev_month_start,
                    DonationBatch.created_at < month_start
                )
            ).scalar() or 0.0
            
            growth = 0.0
            if prev_month_donations > 0:
                growth = ((month_donations - prev_month_donations) / prev_month_donations) * 100
            
            monthly_trends.append({
                "month": month_start.strftime("%B %Y"),
                "amount": month_donations,
                "donation_count": month_count,
                "growth": growth
            })
        
        # Get impact stories (placeholder - would come from church)
        impact_stories = [
            {
                "title": "Your Impact Matters",
                "description": "Every donation helps support our community programs and outreach efforts.",
                "impact_description": "Your consistent giving enables us to serve more families in need."
            }
        ]
        
        history_data = DonationHistoryData(
            donations=donation_data,
            total_amount=total_amount,
            total_batches=total_batches,
            average_per_batch=average_per_batch,
            impact_score=impact_score,
            monthly_trends=monthly_trends,
            impact_stories=impact_stories
        )
        
        return DonationHistoryResponse(
            success=True,
            data=history_data,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get donation history: {str(e)}"
        )
