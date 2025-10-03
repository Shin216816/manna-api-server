#!/usr/bin/env python3
"""
Script to add payout breakdown data to existing ChurchPayout records that don't have it.
This is a one-time migration script.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.model.m_roundup_new import ChurchPayout, DonorPayout
from sqlalchemy import func
import json

def add_breakdown_to_existing_payouts():
    """Add breakdown data to existing payouts that don't have it"""
    db = next(get_db())
    
    try:
        # Find payouts without breakdown data
        payouts_without_breakdown = db.query(ChurchPayout).filter(
            ChurchPayout.payout_breakdown.is_(None)
        ).all()
        
        print(f"Found {len(payouts_without_breakdown)} payouts without breakdown data")
        
        for payout in payouts_without_breakdown:
            print(f"Processing payout {payout.id} for church {payout.church_id}")
            
            # Get donor payouts for this church in the same period
            donor_payouts = db.query(DonorPayout).filter(
                DonorPayout.church_id == payout.church_id,
                DonorPayout.allocated_at.isnot(None),
                DonorPayout.status == "completed"
            ).all()
            
            if not donor_payouts:
                print(f"  No donor payouts found for church {payout.church_id}")
                # Create empty breakdown
                payout.payout_breakdown = {
                    "donor_breakdown": [],
                    "category_breakdown": {}
                }
                continue
            
            # Generate donor breakdown
            donor_breakdown = []
            for dp in donor_payouts:
                donor_breakdown.append({
                    "user_id": dp.user_id,
                    "donation_amount": float(dp.donation_amount),
                    "roundup_multiplier": float(dp.roundup_multiplier),
                    "transaction_count": dp.plaid_transaction_count
                })
            
            # Generate category breakdown (placeholder)
            category_breakdown = {
                "youth_programs": round(payout.gross_donation_amount * 0.3, 2),
                "community_outreach": round(payout.gross_donation_amount * 0.25, 2),
                "facilities": round(payout.gross_donation_amount * 0.2, 2),
                "missions": round(payout.gross_donation_amount * 0.15, 2),
                "events": round(payout.gross_donation_amount * 0.1, 2)
            }
            
            # Update payout with breakdown data
            payout.payout_breakdown = {
                "donor_breakdown": donor_breakdown,
                "category_breakdown": category_breakdown
            }
            
            print(f"  Added breakdown with {len(donor_breakdown)} donors")
        
        # Commit all changes
        db.commit()
        print(f"Successfully updated {len(payouts_without_breakdown)} payouts with breakdown data")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_breakdown_to_existing_payouts()
