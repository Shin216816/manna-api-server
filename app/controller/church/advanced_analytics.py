"""
Advanced Church Analytics Controller

Handles comprehensive analytics and reporting for church admin dashboard:
- Donation trends over time
- Spending categories analysis
- Top merchants analysis
- Growth metrics and forecasting
- Revenue analytics
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, extract, case
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import math

from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
from app.services.plaid_client import get_transactions
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from fastapi import HTTPException


@handle_controller_errors
def get_donation_trends_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "monthly",
    db: Session = None
) -> ResponseFactory:
    """Get comprehensive donation trends analytics"""
    try:
        # Validate church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise UserNotFoundError("Church not found")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not start_date:
            if period == "monthly":
                start_date = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
            else:  # daily
                start_date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

        # Convert to datetime objects
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        # Get donation data
        query = db.query(DonorPayout).filter(
            DonorPayout.church_id == church_id,
            DonorPayout.status == "completed",
            DonorPayout.created_at >= start_dt,
            DonorPayout.created_at <= end_dt
        )

        if period == "monthly":
            # Group by month
            donations = query.with_entities(
                extract('year', DonorPayout.created_at).label('year'),
                extract('month', DonorPayout.created_at).label('month'),
                func.sum(DonorPayout.donation_amount).label('total_amount'),
                func.count(DonorPayout.id).label('donation_count'),
                func.count(func.distinct(DonorPayout.user_id)).label('unique_donors')
            ).group_by(
                extract('year', DonorPayout.created_at),
                extract('month', DonorPayout.created_at)
            ).order_by(
                extract('year', DonorPayout.created_at),
                extract('month', DonorPayout.created_at)
            ).all()
        else:  # daily
            # Group by day
            donations = query.with_entities(
                func.date(DonorPayout.created_at).label('date'),
                func.sum(DonorPayout.donation_amount).label('total_amount'),
                func.count(DonorPayout.id).label('donation_count'),
                func.count(func.distinct(DonorPayout.user_id)).label('unique_donors')
            ).group_by(
                func.date(DonorPayout.created_at)
            ).order_by(
                func.date(DonorPayout.created_at)
            ).all()

        # Format data for frontend
        trends_data = []
        for donation in donations:
            if period == "monthly":
                trends_data.append({
                    "period": f"{int(donation.year)}-{int(donation.month):02d}",
                    "total_amount": float(donation.total_amount or 0),
                    "donation_count": donation.donation_count or 0,
                    "unique_donors": donation.unique_donors or 0,
                    "average_donation": float(donation.total_amount or 0) / max(donation.donation_count or 1, 1)
                })
            else:
                trends_data.append({
                    "period": donation.date.strftime("%Y-%m-%d"),
                    "total_amount": float(donation.total_amount or 0),
                    "donation_count": donation.donation_count or 0,
                    "unique_donors": donation.unique_donors or 0,
                    "average_donation": float(donation.total_amount or 0) / max(donation.donation_count or 1, 1)
                })

        # Calculate growth metrics
        if len(trends_data) >= 2:
            current_period = trends_data[-1]["total_amount"]
            previous_period = trends_data[-2]["total_amount"]
            growth_rate = ((current_period - previous_period) / max(previous_period, 1)) * 100
        else:
            growth_rate = 0.0

        # Calculate total metrics
        total_amount = sum(item["total_amount"] for item in trends_data)
        total_donations = sum(item["donation_count"] for item in trends_data)
        total_unique_donors = max(item["unique_donors"] for item in trends_data) if trends_data else 0

        return ResponseFactory.success(
            message="Donation trends analytics retrieved successfully",
            data={
                "trends": trends_data,
                "summary": {
                    "total_amount": total_amount,
                    "total_donations": total_donations,
                    "total_unique_donors": total_unique_donors,
                    "average_donation": total_amount / max(total_donations, 1),
                    "growth_rate": round(growth_rate, 2)
                },
                "period": period,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting donation trends analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get donation trends analytics")


@handle_controller_errors
def get_spending_categories_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    db: Session = None
) -> ResponseFactory:
    """Get spending categories analytics from donor transactions"""
    try:
        # Validate church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise UserNotFoundError("Church not found")

        # Set default date range
        if not end_date:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

        # Get church donors
        donors = db.query(User).filter(
            User.church_id == church_id,
            User.role == "donor",
            User.is_active == True
        ).all()

        if not donors:
            return ResponseFactory.success(
                message="No donors found for analytics",
                data={"categories": [], "summary": {}}
            )

        # Get spending data from Plaid for all donors
        categories_data = {}
        total_spending = 0.0
        total_transactions = 0

        for donor in donors:
            plaid_item = db.query(PlaidItem).filter(
                PlaidItem.user_id == donor.id,
                PlaidItem.status == "active"
            ).first()

            if plaid_item:
                try:
                    # Get transactions from Plaid
                    transactions_data = get_transactions(
                        access_token=plaid_item.access_token,
                        days_back=90
                    )
                    
                    transactions = transactions_data.get("transactions", [])
                    
                    for transaction in transactions:
                        if transaction["amount"] < 0:  # Spending transactions
                            amount = abs(transaction["amount"])
                            categories = transaction.get("category", [])
                            
                            if categories:
                                # Use the first category as primary
                                primary_category = categories[0]
                                
                                if primary_category not in categories_data:
                                    categories_data[primary_category] = {
                                        "category": primary_category,
                                        "total_amount": 0.0,
                                        "transaction_count": 0,
                                        "donors_count": set()
                                    }
                                
                                categories_data[primary_category]["total_amount"] += amount
                                categories_data[primary_category]["transaction_count"] += 1
                                categories_data[primary_category]["donors_count"].add(donor.id)
                                
                                total_spending += amount
                                total_transactions += 1

                except Exception as e:
                    logging.error(f"Error getting transactions for donor {donor.id}: {str(e)}")
                    continue

        # Convert to list and sort by total amount
        categories_list = []
        for category, data in categories_data.items():
            categories_list.append({
                "category": category,
                "total_amount": round(data["total_amount"], 2),
                "transaction_count": data["transaction_count"],
                "donors_count": len(data["donors_count"]),
                "percentage": round((data["total_amount"] / max(total_spending, 1)) * 100, 2)
            })

        categories_list.sort(key=lambda x: x["total_amount"], reverse=True)
        categories_list = categories_list[:limit]

        return ResponseFactory.success(
            message="Spending categories analytics retrieved successfully",
            data={
                "categories": categories_list,
                "summary": {
                    "total_spending": round(total_spending, 2),
                    "total_transactions": total_transactions,
                    "unique_categories": len(categories_data),
                    "average_transaction": round(total_spending / max(total_transactions, 1), 2)
                },
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting spending categories analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get spending categories analytics")


@handle_controller_errors
def get_top_merchants_analytics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    db: Session = None
) -> ResponseFactory:
    """Get top merchants analytics from donor transactions"""
    try:
        # Validate church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise UserNotFoundError("Church not found")

        # Set default date range
        if not end_date:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

        # Get church donors
        donors = db.query(User).filter(
            User.church_id == church_id,
            User.role == "donor",
            User.is_active == True
        ).all()

        if not donors:
            return ResponseFactory.success(
                message="No donors found for analytics",
                data={"merchants": [], "summary": {}}
            )

        # Get merchant data from Plaid for all donors
        merchants_data = {}
        total_spending = 0.0
        total_transactions = 0

        for donor in donors:
            plaid_item = db.query(PlaidItem).filter(
                PlaidItem.user_id == donor.id,
                PlaidItem.status == "active"
            ).first()

            if plaid_item:
                try:
                    # Get transactions from Plaid
                    transactions_data = get_transactions(
                        access_token=plaid_item.access_token,
                        days_back=90
                    )
                    
                    transactions = transactions_data.get("transactions", [])
                    
                    for transaction in transactions:
                        if transaction["amount"] < 0:  # Spending transactions
                            amount = abs(transaction["amount"])
                            merchant = transaction.get("merchant_name") or transaction.get("name", "Unknown")
                            
                            if merchant not in merchants_data:
                                merchants_data[merchant] = {
                                    "merchant": merchant,
                                    "total_amount": 0.0,
                                    "transaction_count": 0,
                                    "donors_count": set()
                                }
                            
                            merchants_data[merchant]["total_amount"] += amount
                            merchants_data[merchant]["transaction_count"] += 1
                            merchants_data[merchant]["donors_count"].add(donor.id)
                            
                            total_spending += amount
                            total_transactions += 1

                except Exception as e:
                    logging.error(f"Error getting transactions for donor {donor.id}: {str(e)}")
                    continue

        # Convert to list and sort by total amount
        merchants_list = []
        for merchant, data in merchants_data.items():
            merchants_list.append({
                "merchant": merchant,
                "total_amount": round(data["total_amount"], 2),
                "transaction_count": data["transaction_count"],
                "donors_count": len(data["donors_count"]),
                "percentage": round((data["total_amount"] / max(total_spending, 1)) * 100, 2)
            })

        merchants_list.sort(key=lambda x: x["total_amount"], reverse=True)
        merchants_list = merchants_list[:limit]

        return ResponseFactory.success(
            message="Top merchants analytics retrieved successfully",
            data={
                "merchants": merchants_list,
                "summary": {
                    "total_spending": round(total_spending, 2),
                    "total_transactions": total_transactions,
                    "unique_merchants": len(merchants_data),
                    "average_transaction": round(total_spending / max(total_transactions, 1), 2)
                },
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting top merchants analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get top merchants analytics")


@handle_controller_errors
def get_growth_metrics_analytics(
    church_id: int,
    period: str = "monthly",
    db: Session = None
) -> ResponseFactory:
    """Get growth metrics and forecasting analytics"""
    try:
        # Validate church exists
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise UserNotFoundError("Church not found")

        # Get current and previous period data
        now = datetime.now(timezone.utc)
        
        if period == "monthly":
            current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_start = (current_start - timedelta(days=1)).replace(day=1)
            previous_end = current_start - timedelta(days=1)
        else:  # weekly
            current_start = now - timedelta(days=now.weekday())
            current_start = current_start.replace(hour=0, minute=0, second=0, microsecond=0)
            previous_start = current_start - timedelta(days=7)
            previous_end = current_start - timedelta(days=1)

        # Get current period data
        current_donations = db.query(DonorPayout).filter(
            DonorPayout.church_id == church_id,
            DonorPayout.status == "completed",
            DonorPayout.created_at >= current_start
        ).all()

        # Get previous period data
        previous_donations = db.query(DonorPayout).filter(
            DonorPayout.church_id == church_id,
            DonorPayout.status == "completed",
            DonorPayout.created_at >= previous_start,
            DonorPayout.created_at <= previous_end
        ).all()

        # Calculate current period metrics
        current_amount = sum(float(d.donation_amount) for d in current_donations)
        current_count = len(current_donations)
        current_donors = len(set(d.user_id for d in current_donations))

        # Calculate previous period metrics
        previous_amount = sum(float(d.donation_amount) for d in previous_donations)
        previous_count = len(previous_donations)
        previous_donors = len(set(d.user_id for d in previous_donations))

        # Calculate growth rates
        revenue_growth = ((current_amount - previous_amount) / max(previous_amount, 1)) * 100
        donation_growth = ((current_count - previous_count) / max(previous_count, 1)) * 100
        donor_growth = ((current_donors - previous_donors) / max(previous_donors, 1)) * 100

        # Calculate average donation growth
        current_avg = current_amount / max(current_count, 1)
        previous_avg = previous_amount / max(previous_count, 1)
        avg_donation_growth = ((current_avg - previous_avg) / max(previous_avg, 1)) * 100

        # Simple forecasting (linear trend)
        if len(current_donations) > 0 and len(previous_donations) > 0:
            # Calculate trend
            trend_factor = current_amount / max(previous_amount, 1)
            
            # Forecast next period
            if period == "monthly":
                next_period_forecast = current_amount * trend_factor
            else:
                next_period_forecast = current_amount * trend_factor
        else:
            next_period_forecast = current_amount

        return ResponseFactory.success(
            message="Growth metrics analytics retrieved successfully",
            data={
                "current_period": {
                    "amount": round(current_amount, 2),
                    "donation_count": current_count,
                    "donor_count": current_donors,
                    "average_donation": round(current_avg, 2)
                },
                "previous_period": {
                    "amount": round(previous_amount, 2),
                    "donation_count": previous_count,
                    "donor_count": previous_donors,
                    "average_donation": round(previous_avg, 2)
                },
                "growth_rates": {
                    "revenue_growth": round(revenue_growth, 2),
                    "donation_growth": round(donation_growth, 2),
                    "donor_growth": round(donor_growth, 2),
                    "average_donation_growth": round(avg_donation_growth, 2)
                },
                "forecast": {
                    "next_period_forecast": round(next_period_forecast, 2),
                    "trend_factor": round(trend_factor, 2) if 'trend_factor' in locals() else 1.0
                },
                "period": period
            }
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting growth metrics analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get growth metrics analytics")
