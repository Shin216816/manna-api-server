from fastapi import APIRouter, HTTPException
from app.router.v1.donor.auth import router as auth_router
from app.router.v1.donor.profile import router as profile_router
from app.router.v1.donor.dashboard import router as dashboard_router
from app.router.v1.donor.roundups import router as roundups_router
from app.router.v1.donor.roundup_collection import router as roundup_collection_router
from app.router.v1.donor.donations import router as donations_router
from app.router.v1.donor.bank import router as bank_router
from app.router.v1.donor.bank_linking import router as bank_linking_router
from app.router.v1.donor.settings import router as settings_router
from app.router.v1.donor.invite import router as invite_router
from app.router.v1.donor.google_oauth import router as google_oauth_router
from app.router.v1.donor.apple_oauth import router as apple_oauth_router
from app.router.v1.donor.payments import router as payments_router
from app.router.v1.donor.payment_methods import router as payment_methods_router
# from app.router.v1.donor.enhanced_payments import router as enhanced_payments_router  # Deleted - consolidated into payments.py
from app.router.v1.donor.consent import router as consent_router
from app.router.v1.donor.roundup_processing import router as roundup_processing_router
from app.router.v1.donor.email_verification import router as email_verification_router
from app.router.v1.donor.pause_resume import router as pause_resume_router
from app.router.v1.donor.donation_history import router as donation_history_router
from app.router.v1.donor.transactions import router as transactions_router
from app.router.v1.donor.notifications import router as notifications_router

donor_router = APIRouter(tags=["Donor"])

# No redirect handlers needed - FastAPI handles trailing slashes automatically

# Include all donor sub-routers
donor_router.include_router(auth_router, prefix="/auth", tags=["Donor Authentication"])
donor_router.include_router(profile_router, prefix="/profile", tags=["Donor Profile"])
donor_router.include_router(dashboard_router, prefix="/dashboard", tags=["Donor Dashboard"])
donor_router.include_router(roundups_router, prefix="/roundups", tags=["Donor Roundups"])
donor_router.include_router(roundup_collection_router, prefix="/roundup-collection", tags=["Donor Round-up Collection"])
donor_router.include_router(donations_router, prefix="/donations", tags=["Donor Donations"])
donor_router.include_router(bank_router, prefix="/bank", tags=["Donor Banking"])
donor_router.include_router(bank_linking_router, prefix="/bank-linking", tags=["Donor Bank Linking"])
donor_router.include_router(settings_router, prefix="/settings", tags=["Donor Settings"])
donor_router.include_router(invite_router, prefix="/invite", tags=["Donor Invites"])
donor_router.include_router(google_oauth_router, prefix="/google-oauth", tags=["Donor Google OAuth"])
donor_router.include_router(apple_oauth_router, prefix="/apple-oauth", tags=["Donor Apple OAuth"])
donor_router.include_router(payments_router, prefix="/payments", tags=["Donor Payments"])
donor_router.include_router(payment_methods_router, prefix="/payment-methods", tags=["Donor Payment Methods"])
# donor_router.include_router(enhanced_payments_router, prefix="/enhanced-payments", tags=["Donor Enhanced Payments"])  # Deleted - consolidated into payments.py
donor_router.include_router(consent_router, prefix="/consent", tags=["Donor Consent"])
donor_router.include_router(roundup_processing_router, prefix="/roundup-processing", tags=["Donor Roundup Processing"])
donor_router.include_router(email_verification_router, prefix="/email-verification", tags=["Donor Email Verification"])
donor_router.include_router(pause_resume_router, prefix="/pause-resume", tags=["Donor Pause/Resume"])
donor_router.include_router(donation_history_router, prefix="/donation-history", tags=["Donor Donation History"])
donor_router.include_router(transactions_router, prefix="/transactions", tags=["Donor Transactions"])
donor_router.include_router(notifications_router, prefix="/notifications", tags=["Donor Notifications"])
