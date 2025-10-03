# REMOVED: ReferralCommission model
# This model was redundant with church_referrals table functionality.
# The church_referrals table already provides all necessary commission tracking:
# - total_commission_earned: Tracks cumulative commission amount
# - commission_paid: Boolean flag for payment status
# - payout_status: Tracks payout processing status
# - payout_amount: Stores actual payout amount
# - payout_date: Records when commission was paid
# - stripe_transfer_id: Links to Stripe transfer for audit trail
#
# The referral_commissions table was dropped by the remove_referral_commissions_table.py migration.
#
# For referral commission functionality, use:
# - app.model.m_church_referral.ChurchReferral
