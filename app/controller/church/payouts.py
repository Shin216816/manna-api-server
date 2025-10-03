from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from sqlalchemy import func

from app.model.m_church import Church
from app.model.m_roundup_new import ChurchPayout
from app.core.messages import get_auth_message
from app.core.responses import ResponseFactory, SuccessResponse
from app.tasks.process_church_payouts import create_monthly_church_payouts


def get_payout_history(
    church_id: int, db: Session, page: int = 1, limit: int = 20
) -> SuccessResponse:
    """Get church payout history"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        offset = (page - 1) * limit

        payouts = (
            db.query(ChurchPayout)
            .filter(ChurchPayout.church_id == church_id)
            .order_by(ChurchPayout.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        total_count = (
            db.query(func.count(ChurchPayout.id))
            .filter(ChurchPayout.church_id == church_id)
            .scalar()
        )

        payouts_data = []
        for payout in payouts:
            # Generate a reference number based on payout ID and date
            reference = f"PAY-{payout.id:06d}-{payout.created_at.strftime('%Y%m')}"

            payouts_data.append(
                {
                    "id": payout.id,
                    "amount": float(payout.net_payout_amount),  # Use net_payout_amount instead of amount
                    "gross_amount": float(payout.gross_donation_amount),
                    "system_fee": float(payout.system_fee_amount),
                    "status": payout.status,
                    "created_at": payout.created_at.isoformat(),
                    "processed_at": (
                        payout.processed_at.isoformat() if payout.processed_at else None
                    ),
                    "description": f"Payout for {payout.period_start} to {payout.period_end} ({payout.donor_count} donors, {payout.donation_count} donations)",
                    "stripe_transfer_id": payout.stripe_transfer_id,
                    "period_start": payout.period_start,  # Already a string
                    "period_end": payout.period_end,  # Already a string
                    "currency": "USD",  # ChurchPayout doesn't have currency field, default to USD
                    "reference": reference,
                    "failure_reason": payout.failure_reason,
                    "donor_count": payout.donor_count,
                    "donation_count": payout.donation_count,
                    "payout_breakdown": payout.payout_breakdown,
                }
            )

        return ResponseFactory.success(
            message="Payout history retrieved successfully",
            data={
                "payouts": payouts_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get payout history")


def get_payout_details(payout_id: int, church_id: int, db: Session) -> SuccessResponse:
    """Get specific payout details"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        payout = (
            db.query(ChurchPayout)
            .filter(ChurchPayout.id == payout_id, ChurchPayout.church_id == church_id)
            .first()
        )

        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")

        # Generate a reference number based on payout ID and date
        reference = f"PAY-{payout.id:06d}-{payout.created_at.strftime('%Y%m')}"

        return ResponseFactory.success(
            message="Payout details retrieved successfully",
            data={
                "id": payout.id,
                "amount": float(payout.net_payout_amount),
                "gross_amount": float(payout.gross_donation_amount),
                "system_fee": float(payout.system_fee_amount),
                "status": payout.status,
                "created_at": payout.created_at.isoformat(),
                "processed_at": (
                    payout.processed_at.isoformat() if payout.processed_at else None
                ),
                "reference": reference,
                "stripe_transfer_id": payout.stripe_transfer_id,
                "failure_reason": payout.failure_reason,
                "description": f"Payout for {payout.period_start} to {payout.period_end} ({payout.donor_count} donors, {payout.donation_count} donations)",
                "currency": "USD",
                "period_start": payout.period_start,
                "period_end": payout.period_end,
                "donor_count": payout.donor_count,
                "donation_count": payout.donation_count,
                "payout_breakdown": payout.payout_breakdown,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get payout details")


def get_payout_status(church_id: int, db: Session) -> SuccessResponse:
    """Get church payout status summary"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get payout statistics by status
        status_stats = (
            db.query(
                ChurchPayout.status,
                func.sum(ChurchPayout.net_payout_amount).label("total_amount"),
                func.count(ChurchPayout.id).label("count"),
            )
            .filter(ChurchPayout.church_id == church_id)
            .group_by(ChurchPayout.status)
            .all()
        )

        status_summary = {}
        for stat in status_stats:
            status_summary[stat.status] = {
                "total_amount": float(stat.total_amount),
                "count": stat.count,
            }

        # Get pending amount
        pending_amount = status_summary.get("pending", {}).get("total_amount", 0.0)
        completed_amount = status_summary.get("completed", {}).get("total_amount", 0.0)
        failed_amount = status_summary.get("failed", {}).get("total_amount", 0.0)

        return ResponseFactory.success(
            message="Payout status retrieved successfully",
            data={
                "pending_amount": pending_amount,
                "completed_amount": completed_amount,
                "failed_amount": failed_amount,
                "total_payouts": sum(stat.count for stat in status_stats),
                "status_breakdown": status_summary,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get payout status")
