"""
Comprehensive Admin Dashboard Controller

Provides comprehensive dashboard functionality for internal admin:
- Real-time platform metrics
- Advanced analytics and insights
- System health monitoring
- Business intelligence features
- Payout management and scheduling
- Donor analytics and patterns
- Church performance tracking
- Financial metrics and reporting
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, and_, or_
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import json

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_donation_preference import DonationPreference
from app.model.m_church_referral import ChurchReferral
from app.model.m_payout import Payout
from app.model.m_admin_user import AdminUser
from app.core.responses import ResponseFactory


def get_dashboard_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get comprehensive dashboard overview with all necessary data"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")

        # Parse dates
        start_dt = parse_date(start_date) if start_date else None
        end_dt = parse_date(end_date) if end_date else None

        # Get current time for real-time calculations
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)

        # ===== PLATFORM OVERVIEW METRICS =====
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        verified_users = db.query(func.count(User.id)).filter(User.is_email_verified == True).scalar()
        
        total_churches = db.query(func.count(Church.id)).scalar()
        active_churches = db.query(func.count(Church.id)).filter(Church.is_active == True).scalar()
        approved_churches = db.query(func.count(Church.id)).filter(Church.kyc_status == "approved").scalar()

        # ===== REVENUE & FINANCIAL METRICS =====
        # Total revenue from DonationBatch (completed donations)
        total_revenue_query = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed"
        )
        if start_dt:
            total_revenue_query = total_revenue_query.filter(DonationBatch.created_at >= start_dt)
        if end_dt:
            total_revenue_query = total_revenue_query.filter(DonationBatch.created_at <= end_dt)
        
        total_revenue = float(total_revenue_query.scalar() or 0.0)
        platform_fee = total_revenue * 0.05  # 5% platform fee
        net_revenue = total_revenue - platform_fee

        # Today's metrics
        today_revenue = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= today_start
        ).scalar() or 0.0)

        # Yesterday's metrics for comparison
        yesterday_revenue = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= yesterday_start,
            DonationBatch.created_at < today_start
        ).scalar() or 0.0)

        # This week's revenue
        week_revenue = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= week_ago
        ).scalar() or 0.0)

        # This month's revenue
        month_revenue = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= month_ago
        ).scalar() or 0.0)

        # ===== DONATION METRICS =====
        total_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "completed"
        ).scalar()
        
        today_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= today_start
        ).scalar()

        # Average donation amount
        avg_donation = float(db.query(func.avg(DonationBatch.amount)).filter(
            DonationBatch.status == "completed"
        ).scalar() or 0.0)

        # ===== ACTIVE DONORS =====
        # Users with active donation preferences
        active_donors = db.query(func.count(User.id.distinct())).join(
            DonationPreference, User.id == DonationPreference.user_id
        ).filter(
            DonationPreference.pause == False,
            DonationPreference.roundups_enabled == True
        ).scalar()

        # ===== GROWTH CALCULATIONS =====
        revenue_growth = calculate_growth_rate(today_revenue, yesterday_revenue)
        user_growth = calculate_user_growth(db, today_start, yesterday_start)
        church_growth = calculate_church_growth(db, today_start, yesterday_start)
        donation_growth = calculate_donation_growth(db, today_start, yesterday_start)

        # ===== RECENT ACTIVITY (last 24 hours) =====
        recent_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= yesterday_start,
            DonationBatch.status == "completed"
        ).scalar()

        recent_users = db.query(func.count(User.id)).filter(
            User.created_at >= yesterday_start
        ).scalar()

        recent_churches = db.query(func.count(Church.id)).filter(
            Church.created_at >= yesterday_start
        ).scalar()

        # ===== KYC STATUS OVERVIEW =====
        kyc_pending = db.query(func.count(Church.id)).filter(
            Church.kyc_status == "pending"
        ).scalar()

        kyc_approved = db.query(func.count(Church.id)).filter(
            Church.kyc_status == "approved"
        ).scalar()

        kyc_rejected = db.query(func.count(Church.id)).filter(
            Church.kyc_status == "rejected"
        ).scalar()

        kyc_not_submitted = db.query(func.count(Church.id)).filter(
            Church.kyc_status == "not_submitted"
        ).scalar()

        # ===== PAYOUT MANAGEMENT =====
        # Pending payouts (DonationBatch status pending)
        pending_payouts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "pending"
        ).scalar()

        # Completed payouts
        completed_payouts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "completed"
        ).scalar()

        # Failed payouts
        failed_payouts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "failed"
        ).scalar()

        # Total payout amount
        total_payout_amount = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.status == "completed"
        ).scalar() or 0.0)

        # Next payout calculation (assuming weekly payouts on Fridays)
        next_payout_date = calculate_next_payout_date()
        days_until_payout = (next_payout_date - now).days

        # ===== TOP PERFORMING CHURCHES =====
        top_churches = db.query(
            Church.id,
            Church.name,
            Church.kyc_status,
            func.sum(DonationBatch.amount).label("revenue"),
            func.count(DonationBatch.id).label("donation_count"),
            func.count(func.distinct(DonationBatch.user_id)).label("donor_count")
        ).join(DonationBatch, Church.id == DonationBatch.church_id).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= month_ago
        ).group_by(Church.id, Church.name, Church.kyc_status).order_by(
            func.sum(DonationBatch.amount).desc()
        ).limit(10).all()

        # ===== DONOR ANALYTICS =====
        # Donation frequency distribution
        donation_frequencies = db.query(
            DonationPreference.frequency,
            func.count(DonationPreference.id).label("count")
        ).group_by(DonationPreference.frequency).all()

        # Roundup multiplier distribution
        multiplier_distribution = db.query(
            DonationPreference.multiplier,
            func.count(DonationPreference.id).label("count")
        ).group_by(DonationPreference.multiplier).all()

        # ===== REFERRAL SYSTEM =====
        total_referrals = db.query(func.count(ChurchReferral.id)).scalar()
        active_referrals = db.query(func.count(ChurchReferral.id)).filter(
            ChurchReferral.status == "active"
        ).scalar()
        
        total_commission_earned = float(db.query(func.sum(ChurchReferral.total_commission_earned)).scalar() or 0.0)

        # ===== SYSTEM HEALTH =====
        system_health = get_system_health_metrics(db)
        system_alerts = get_system_alerts(db)

        # ===== CHART DATA =====
        revenue_trend = generate_revenue_trend_data(db, start_dt, end_dt)
        user_growth_trend = generate_user_growth_trend_data(db, start_dt, end_dt)
        donation_trend = generate_donation_trend_data(db, start_dt, end_dt)
        church_performance = generate_church_performance_data(db, start_dt, end_dt)

        # ===== REAL-TIME METRICS =====
        # Last hour activity
        last_hour = now - timedelta(hours=1)
        donations_last_hour = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar()

        revenue_last_hour = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar() or 0.0)

        # Active sessions (users who logged in within last hour)
        active_sessions = db.query(func.count(User.id)).filter(
            User.last_login >= last_hour
        ).scalar()

        return ResponseFactory.success(
            message="Comprehensive dashboard overview retrieved successfully",
            data={
                # Platform Overview
                "overview": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "verified_users": verified_users,
                    "total_churches": total_churches,
                    "active_churches": active_churches,
                    "approved_churches": approved_churches,
                    "active_donors": active_donors,
                },
                
                # Financial Metrics
                "revenue": {
                    "total_revenue": round(float(total_revenue), 2),
                    "platform_fee": round(float(platform_fee), 2),
                    "net_revenue": round(float(net_revenue), 2),
                    "today_revenue": round(float(today_revenue), 2),
                    "yesterday_revenue": round(float(yesterday_revenue), 2),
                    "week_revenue": round(float(week_revenue), 2),
                    "month_revenue": round(float(month_revenue), 2),
                    "revenue_growth": round(revenue_growth, 2),
                },
                
                # Donation Metrics
                "donations": {
                    "total_donations": total_donations,
                    "today_donations": today_donations,
                    "average_donation": round(float(avg_donation), 2),
                    "donation_growth": round(donation_growth, 2),
                },
                
                # Growth Metrics
                "growth": {
                    "user_growth": round(user_growth, 2),
                    "church_growth": round(church_growth, 2),
                    "revenue_growth": round(revenue_growth, 2),
                    "donation_growth": round(donation_growth, 2),
                },
                
                # Activity Metrics
                "activity": {
                    "recent_donations": recent_donations,
                    "recent_users": recent_users,
                    "recent_churches": recent_churches,
                    "donations_last_hour": donations_last_hour,
                    "revenue_last_hour": round(float(revenue_last_hour), 2),
                    "active_sessions": active_sessions,
                },
                
                # KYC Status
                "kyc_status": {
                    "pending": kyc_pending,
                    "approved": kyc_approved,
                    "rejected": kyc_rejected,
                    "not_submitted": kyc_not_submitted,
                },
                
                # Payout Management
                "payouts": {
                    "pending_payouts": pending_payouts,
                    "completed_payouts": completed_payouts,
                    "failed_payouts": failed_payouts,
                    "total_payout_amount": round(float(total_payout_amount), 2),
                    "next_payout_date": next_payout_date.isoformat(),
                    "days_until_payout": days_until_payout,
                },
                
                # Top Churches
                "top_churches": [
                    {
                        "id": church_id,
                        "name": church_name,
                        "kyc_status": kyc_status,
                        "revenue": round(float(revenue or 0), 2),
                        "donation_count": count or 0,
                        "donor_count": donor_count or 0
                    }
                    for church_id, church_name, kyc_status, revenue, count, donor_count in top_churches
                ],
                
                # Donor Analytics
                "donor_analytics": {
                    "donation_frequencies": [
                        {"frequency": freq, "count": count}
                        for freq, count in donation_frequencies
                    ],
                    "multiplier_distribution": [
                        {"multiplier": mult, "count": count}
                        for mult, count in multiplier_distribution
                    ],
                },
                
                # Referral System
                "referrals": {
                    "total_referrals": total_referrals,
                    "active_referrals": active_referrals,
                    "total_commission_earned": round(float(total_commission_earned), 2),
                },
                
                # System Health
                "system_health": system_health,
                "system_alerts": system_alerts,
                
                # Chart Data
                "revenue_trend": revenue_trend,
                "user_growth_trend": user_growth_trend,
                "donation_trend": donation_trend,
                "church_performance": church_performance,
                
                # Metadata
                "last_updated": now.isoformat(),
                "data_period": {
                    "start_date": start_dt.isoformat() if start_dt else None,
                    "end_date": end_dt.isoformat() if end_dt else None,
                }
            },
        )

    except Exception as e:
        logging.error(f"Error getting comprehensive dashboard overview: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve comprehensive dashboard overview")


def get_realtime_metrics(db: Session):
    """Get real-time system and business metrics"""
    try:
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        # Real-time business metrics
        donations_last_hour = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar()

        revenue_last_hour = float(db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar() or 0.0)

        # Active sessions (approximate)
        active_sessions = db.query(func.count(User.id)).filter(
            User.last_login >= last_hour
        ).scalar()

        # Processing rate (successful vs total)
        total_attempts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_hour
        ).scalar()
        
        successful_attempts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar()
        
        processing_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 100.0

        # System health metrics
        system_health = get_system_health_metrics(db)

        # Error rates
        error_rate = get_error_rate_metrics(db)

        return ResponseFactory.success(
            message="Real-time metrics retrieved successfully",
            data={
                "business_metrics": {
                    "donations_last_hour": donations_last_hour,
                    "revenue_last_hour": round(float(revenue_last_hour), 2),
                    "active_sessions": active_sessions,
                    "processing_rate": round(processing_rate, 2),
                },
                "system_health": system_health,
                "error_rate": error_rate,
                "timestamp": now.isoformat(),
            },
        )

    except Exception as e:
        logging.error(f"Error getting real-time metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve real-time metrics")


def get_payout_management_data(db: Session):
    """Get comprehensive payout management data"""
    try:
        now = datetime.now(timezone.utc)
        
        # Pending payouts by church - use DonorPayout table (same as payouts page)
        pending_payouts = db.query(
            DonorPayout.church_id,
            Church.name.label('church_name'),
            Church.kyc_status,
            Church.stripe_account_id,
            func.sum(DonorPayout.donation_amount).label('total_amount'),
            func.count(DonorPayout.id).label('donation_count'),
            func.count(func.distinct(DonorPayout.user_id)).label('donor_count'),
            func.min(DonorPayout.processed_at).label('oldest_donation'),
            func.max(DonorPayout.processed_at).label('newest_donation')
        ).join(
            Church, DonorPayout.church_id == Church.id
        ).filter(
            and_(
                DonorPayout.status == "completed",  # Successfully processed
                DonorPayout.allocated_at.is_(None),  # Not yet allocated to church payout
                Church.status == "active",
                Church.kyc_status == "verified"
            )
        ).group_by(
            DonorPayout.church_id, Church.name, Church.kyc_status, Church.stripe_account_id
        ).order_by(
            func.sum(DonorPayout.donation_amount).desc()
        ).all()

        # Payout history (last 30 days) - use ChurchPayout table
        payout_history = db.query(
            func.date(ChurchPayout.created_at).label('date'),
            func.sum(ChurchPayout.net_payout_amount).label('amount'),
            func.count(ChurchPayout.id).label('count')
        ).filter(
            ChurchPayout.status == "completed",
            ChurchPayout.created_at >= now - timedelta(days=30)
        ).group_by(func.date(ChurchPayout.created_at)).order_by(
            func.date(ChurchPayout.created_at).desc()
        ).all()

        # Next payout calculation
        next_payout_date = calculate_next_payout_date()
        days_until_payout = (next_payout_date - now).days

        return ResponseFactory.success(
            message="Payout management data retrieved successfully",
            data={
                "pending_payouts": [
                    {
                        "church_id": payout.church_id,
                        "church_name": payout.church_name,
                        "kyc_status": payout.kyc_status,
                        "total_amount": round(float(payout.total_amount or 0), 2),
                        "donation_count": payout.donation_count or 0,
                        "donor_count": payout.donor_count or 0,
                        "oldest_donation": payout.oldest_donation.isoformat() if payout.oldest_donation else None,
                        "newest_donation": payout.newest_donation.isoformat() if payout.newest_donation else None,
                        "has_stripe_account": bool(payout.stripe_account_id),
                        "days_pending": (now - payout.oldest_donation).days if payout.oldest_donation else 0,
                        "ready_for_payout": bool(payout.stripe_account_id) and (now - payout.oldest_donation).days >= 7 if payout.oldest_donation else False
                    }
                    for payout in pending_payouts
                ],
                "payout_history": [
                    {
                        "date": date.isoformat() if date else None,
                        "amount": round(float(amount or 0), 2),
                        "count": count or 0
                    }
                    for date, amount, count in payout_history
                ],
                "next_payout": {
                    "date": next_payout_date.isoformat(),
                    "days_until": days_until_payout
                },
                "summary": {
                    "total_churches": len(pending_payouts),
                    "total_amount": round(sum(float(payout.total_amount or 0) for payout in pending_payouts), 2),
                    "total_donations": sum(payout.donation_count or 0 for payout in pending_payouts),
                    "total_donors": sum(payout.donor_count or 0 for payout in pending_payouts)
                }
            }
        )

    except Exception as e:
        logging.error(f"Error getting payout management data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payout management data")


def get_donor_analytics(db: Session, start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None):
    """Get comprehensive donor analytics"""
    try:
        # Default to last 30 days if no date range specified
        if not end_dt:
            end_dt = datetime.now(timezone.utc)
        if not start_dt:
            start_dt = end_dt - timedelta(days=30)

        # Donor activity
        active_donors = db.query(func.count(User.id.distinct())).join(
            DonationBatch, User.id == DonationBatch.user_id
        ).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).scalar()

        # Donation patterns
        donation_patterns = db.query(
            DonationPreference.frequency,
            DonationPreference.multiplier,
            func.count(DonationPreference.id).label('count')
        ).group_by(DonationPreference.frequency, DonationPreference.multiplier).all()

        # Top donors
        top_donors = db.query(
            User.id,
            User.first_name,
            User.last_name,
            func.sum(DonationBatch.amount).label('total_donated'),
            func.count(DonationBatch.id).label('donation_count'),
            func.avg(DonationBatch.amount).label('avg_donation')
        ).join(DonationBatch, User.id == DonationBatch.user_id).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).group_by(User.id, User.first_name, User.last_name).order_by(
            func.sum(DonationBatch.amount).desc()
        ).limit(10).all()

        # Donation frequency by day of week
        daily_patterns = db.query(
            func.extract('dow', DonationBatch.created_at).label('day_of_week'),
            func.count(DonationBatch.id).label('count'),
            func.sum(DonationBatch.amount).label('amount')
        ).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).group_by(func.extract('dow', DonationBatch.created_at)).all()

        return ResponseFactory.success(
            message="Donor analytics retrieved successfully",
            data={
                "active_donors": active_donors,
                "donation_patterns": [
                    {
                        "frequency": pattern.frequency,
                        "multiplier": pattern.multiplier,
                        "count": pattern.count
                    }
                    for pattern in donation_patterns
                ],
                "top_donors": [
                    {
                        "id": donor.id,
                        "name": f"{donor.first_name} {donor.last_name}",
                        "total_donated": round(float(total_donated or 0), 2),
                        "donation_count": count or 0,
                        "avg_donation": round(float(avg_donation or 0), 2)
                    }
                    for donor, total_donated, count, avg_donation in top_donors
                ],
                "daily_patterns": [
                    {
                        "day_of_week": int(day or 0),
                        "count": count or 0,
                        "amount": round(float(amount or 0), 2)
                    }
                    for day, count, amount in daily_patterns
                ]
            }
        )

    except Exception as e:
        logging.error(f"Error getting donor analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve donor analytics")


def get_church_performance_analytics(db: Session, start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None):
    """Get comprehensive church performance analytics"""
    try:
        # Default to last 30 days if no date range specified
        if not end_dt:
            end_dt = datetime.now(timezone.utc)
        if not start_dt:
            start_dt = end_dt - timedelta(days=30)

        # Church performance metrics
        church_performance = db.query(
            Church.id,
            Church.name,
            Church.kyc_status,
            Church.status,
            Church.is_active,
            func.sum(DonationBatch.amount).label('total_revenue'),
            func.count(DonationBatch.id).label('donation_count'),
            func.count(func.distinct(DonationBatch.user_id)).label('donor_count'),
            func.avg(DonationBatch.amount).label('avg_donation')
        ).outerjoin(DonationBatch, and_(
            Church.id == DonationBatch.church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        )).group_by(
            Church.id, Church.name, Church.kyc_status, Church.status, Church.is_active
        ).order_by(func.sum(DonationBatch.amount).desc()).all()

        # KYC status distribution
        kyc_distribution = db.query(
            Church.kyc_status,
            func.count(Church.id).label('count')
        ).group_by(Church.kyc_status).all()

        # Church growth over time
        church_growth = db.query(
            func.date(Church.created_at).label('date'),
            func.count(Church.id).label('count')
        ).filter(
            Church.created_at >= start_dt,
            Church.created_at <= end_dt
        ).group_by(func.date(Church.created_at)).order_by(
            func.date(Church.created_at)
        ).all()

        return ResponseFactory.success(
            message="Church performance analytics retrieved successfully",
            data={
                "church_performance": [
                    {
                        "id": church.id,
                        "name": church.name,
                        "kyc_status": church.kyc_status,
                        "status": church.status,
                        "is_active": church.is_active,
                        "total_revenue": round(float(total_revenue or 0), 2),
                        "donation_count": donation_count or 0,
                        "donor_count": donor_count or 0,
                        "avg_donation": round(float(avg_donation or 0), 2)
                    }
                    for church, total_revenue, donation_count, donor_count, avg_donation in church_performance
                ],
                "kyc_distribution": [
                    {
                        "status": status,
                        "count": count
                    }
                    for status, count in kyc_distribution
                ],
                "church_growth": [
                    {
                        "date": date.isoformat() if date else None,
                        "count": count
                    }
                    for date, count in church_growth
                ]
            }
        )

    except Exception as e:
        logging.error(f"Error getting church performance analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve church performance analytics")


def get_system_health_metrics(db: Session) -> Dict[str, Any]:
    """Get comprehensive system health metrics"""
    try:
        now = datetime.now(timezone.utc)
        
        # Database health
        total_users = db.query(func.count(User.id)).scalar()
        total_churches = db.query(func.count(Church.id)).scalar()
        total_donations = db.query(func.count(DonationBatch.id)).scalar()
        
        # Error rates
        failed_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "failed"
        ).scalar()
        
        error_rate = (failed_donations / total_donations * 100) if total_donations > 0 else 0.0
        
        # Processing efficiency
        pending_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "pending"
        ).scalar()
        
        completed_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "completed"
        ).scalar()
        
        processing_efficiency = (completed_donations / (completed_donations + pending_donations) * 100) if (completed_donations + pending_donations) > 0 else 100.0
        
        # System status
        status = "healthy"
        if error_rate > 5.0:
            status = "warning"
        if error_rate > 10.0:
            status = "critical"
        
        return {
            "status": status,
            "cpu_usage": 45.2,  # Placeholder - would integrate with monitoring
            "memory_usage": 67.8,  # Placeholder
            "disk_usage": 23.1,  # Placeholder
            "database_connections": 12,  # Placeholder
            "response_time_avg": 150,  # Placeholder
            "uptime": "99.9%",  # Placeholder
            "error_rate": round(error_rate, 2),
            "processing_efficiency": round(processing_efficiency, 2),
            "total_records": {
                "users": total_users,
                "churches": total_churches,
                "donations": total_donations
            },
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting system health metrics: {str(e)}")
        return {
            "status": "unknown",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_system_alerts(db: Session) -> List[Dict[str, Any]]:
    """Get system alerts and notifications"""
    alerts = []
    now = datetime.now(timezone.utc)
    
    try:
        # Check for high error rates
        total_donations = db.query(func.count(DonationBatch.id)).scalar()
        failed_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "failed"
        ).scalar()
        
        error_rate = (failed_donations / total_donations * 100) if total_donations > 0 else 0.0
        
        if error_rate > 5.0:
            alerts.append({
                "type": "error",
                "title": "High Error Rate",
                "message": f"Error rate is {error_rate:.1f}%, above normal threshold",
                "severity": "high" if error_rate > 10.0 else "medium",
                "timestamp": now.isoformat()
            })

        # Check for pending KYC applications
        pending_kyc = db.query(func.count(Church.id)).filter(
            Church.kyc_status == "pending"
        ).scalar()
        
        if pending_kyc > 10:
            alerts.append({
                "type": "kyc",
                "title": "High KYC Pending Count",
                "message": f"{pending_kyc} KYC applications pending review",
                "severity": "medium",
                "timestamp": now.isoformat()
            })

        # Check for failed payouts
        failed_payouts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "failed"
        ).scalar()
        
        if failed_payouts > 0:
            alerts.append({
                "type": "payout",
                "title": "Failed Payouts",
                "message": f"{failed_payouts} payouts have failed and need attention",
                "severity": "high",
                "timestamp": now.isoformat()
            })

        # Check for inactive churches
        inactive_churches = db.query(func.count(Church.id)).filter(
            Church.is_active == False
        ).scalar()
        
        if inactive_churches > 5:
            alerts.append({
                "type": "church",
                "title": "Inactive Churches",
                "message": f"{inactive_churches} churches are currently inactive",
                "severity": "low",
                "timestamp": now.isoformat()
            })

    except Exception as e:
        logging.error(f"Error generating system alerts: {str(e)}")
        alerts.append({
            "type": "system",
            "title": "Alert System Error",
            "message": f"Unable to generate system alerts: {str(e)}",
            "severity": "medium",
            "timestamp": now.isoformat()
        })

    return alerts


def get_error_rate_metrics(db: Session) -> float:
    """Get error rate metrics"""
    try:
        total_donations = db.query(func.count(DonationBatch.id)).scalar()
        failed_donations = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "failed"
        ).scalar()
        
        return (failed_donations / total_donations * 100) if total_donations > 0 else 0.0
    except Exception as e:
        logging.error(f"Error calculating error rate: {str(e)}")
        return 0.0


def calculate_growth_rate(current: float, previous: float) -> float:
    """Calculate growth rate percentage"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


def calculate_user_growth(db: Session, current_start: datetime, previous_start: datetime) -> float:
    """Calculate user growth rate"""
    current_users = db.query(func.count(User.id)).filter(
        User.created_at >= current_start
    ).scalar()
    
    previous_users = db.query(func.count(User.id)).filter(
        User.created_at >= previous_start,
        User.created_at < current_start
    ).scalar()
    
    return calculate_growth_rate(current_users, previous_users)


def calculate_church_growth(db: Session, current_start: datetime, previous_start: datetime) -> float:
    """Calculate church growth rate"""
    current_churches = db.query(func.count(Church.id)).filter(
        Church.created_at >= current_start
    ).scalar()
    
    previous_churches = db.query(func.count(Church.id)).filter(
        Church.created_at >= previous_start,
        Church.created_at < current_start
    ).scalar()
    
    return calculate_growth_rate(current_churches, previous_churches)


def calculate_donation_growth(db: Session, current_start: datetime, previous_start: datetime) -> float:
    """Calculate donation growth rate"""
    current_donations = db.query(func.count(DonationBatch.id)).filter(
        DonationBatch.created_at >= current_start,
        DonationBatch.status == "completed"
    ).scalar()
    
    previous_donations = db.query(func.count(DonationBatch.id)).filter(
        DonationBatch.created_at >= previous_start,
        DonationBatch.created_at < current_start,
        DonationBatch.status == "completed"
    ).scalar()
    
    return calculate_growth_rate(current_donations, previous_donations)


def calculate_next_payout_date() -> datetime:
    """Calculate next payout date (assuming weekly payouts on Fridays at 2 PM UTC)"""
    now = datetime.now(timezone.utc)
    
    # Find next Friday at 2 PM UTC
    days_ahead = 4 - now.weekday()  # Friday is 4
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    
    next_friday = now + timedelta(days=days_ahead)
    next_friday = next_friday.replace(hour=14, minute=0, second=0, microsecond=0)
    
    return next_friday


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")


def generate_revenue_trend_data(db: Session, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> List[Dict[str, Any]]:
    """Generate revenue trend data for the last 6 months"""
    try:
        # Default to last 6 months if no date range specified
        if not end_dt:
            end_dt = datetime.now(timezone.utc)
        if not start_dt:
            start_dt = end_dt - timedelta(days=180)
        
        # Generate monthly data points
        trend_data = []
        current_date = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_dt:
            month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            if month_end > end_dt:
                month_end = end_dt
            
            # Get revenue for this month
            monthly_revenue = float(db.query(func.sum(DonationBatch.amount)).filter(
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_date,
                DonationBatch.created_at <= month_end
            ).scalar() or 0.0)
            
            # Get donation count for this month
            monthly_count = db.query(func.count(DonationBatch.id)).filter(
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_date,
                DonationBatch.created_at <= month_end
            ).scalar() or 0
            
            trend_data.append({
                "month": current_date.strftime("%b %Y"),
                "revenue": round(float(monthly_revenue), 2),
                "count": monthly_count
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return trend_data
        
    except Exception as e:
        logging.error(f"Error generating revenue trend data: {str(e)}")
        return []


def generate_user_growth_trend_data(db: Session, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> List[Dict[str, Any]]:
    """Generate user growth trend data for the last 6 months"""
    try:
        # Default to last 6 months if no date range specified
        if not end_dt:
            end_dt = datetime.now(timezone.utc)
        if not start_dt:
            start_dt = end_dt - timedelta(days=180)
        
        # Generate monthly data points
        trend_data = []
        current_date = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_dt:
            month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            if month_end > end_dt:
                month_end = end_dt
            
            # Get new users for this month
            monthly_users = db.query(func.count(User.id)).filter(
                User.created_at >= current_date,
                User.created_at <= month_end
            ).scalar() or 0
            
            trend_data.append({
                "month": current_date.strftime("%b %Y"),
                "users": monthly_users
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return trend_data
        
    except Exception as e:
        logging.error(f"Error generating user growth trend data: {str(e)}")
        return []


def generate_donation_trend_data(db: Session, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> List[Dict[str, Any]]:
    """Generate donation trend data for the last 6 months"""
    try:
        # Default to last 6 months if no date range specified
        if not end_dt:
            end_dt = datetime.now(timezone.utc)
        if not start_dt:
            start_dt = end_dt - timedelta(days=180)
        
        # Generate monthly data points
        trend_data = []
        current_date = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_dt:
            month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            if month_end > end_dt:
                month_end = end_dt
            
            # Get donations for this month
            monthly_donations = db.query(func.count(DonationBatch.id)).filter(
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_date,
                DonationBatch.created_at <= month_end
            ).scalar() or 0
            
            # Get unique donors for this month
            monthly_donors = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_date,
                DonationBatch.created_at <= month_end
            ).scalar() or 0
            
            trend_data.append({
                "month": current_date.strftime("%b %Y"),
                "donations": monthly_donations,
                "donors": monthly_donors
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return trend_data
        
    except Exception as e:
        logging.error(f"Error generating donation trend data: {str(e)}")
        return []


def generate_church_performance_data(db: Session, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> List[Dict[str, Any]]:
    """Generate church performance data for the last 6 months"""
    try:
        # Default to last 6 months if no date range specified
        if not end_dt:
            end_dt = datetime.now(timezone.utc)
        if not start_dt:
            start_dt = end_dt - timedelta(days=180)
        
        # Get top performing churches
        church_performance = db.query(
            Church.id,
            Church.name,
            func.sum(DonationBatch.amount).label('total_revenue'),
            func.count(DonationBatch.id).label('donation_count'),
            func.count(func.distinct(DonationBatch.user_id)).label('donor_count')
        ).join(DonationBatch, Church.id == DonationBatch.church_id).filter(
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).group_by(Church.id, Church.name).order_by(
            func.sum(DonationBatch.amount).desc()
        ).limit(10).all()
        
        return [
            {
                "church_id": church_id,
                "church_name": church_name,
                "total_revenue": round(float(total_revenue or 0), 2),
                "donation_count": donation_count or 0,
                "donor_count": donor_count or 0
            }
            for church_id, church_name, total_revenue, donation_count, donor_count in church_performance
        ]
        
    except Exception as e:
        logging.error(f"Error generating church performance data: {str(e)}")
        return []