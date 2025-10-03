import stripe
import logging
import json
from typing import Dict, Optional, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.utils.stripe_client import stripe
from app.model.m_church import Church
from app.model.m_beneficial_owner import BeneficialOwner
from app.model.m_audit_log import AuditLog
from app.core.exceptions import StripeError


class KYCService:
    """Service for handling KYC workflow with Stripe Connect"""

    @staticmethod
    def create_stripe_connect_account(church: Church, db: Session) -> Dict[str, Any]:
        """Create a Stripe Express connected account for the church"""
        try:
            # Check Stripe configuration
            if not stripe.api_key:

                raise Exception("Stripe API key is not configured")

            # Validate church data
            if not church.email or not church.email.strip():

                raise Exception(
                    "Church email address is required for Stripe account creation"
                )

            if not church.name or not church.name.strip():

                raise Exception("Church name is required for Stripe account creation")

            # Create Express account for platform-first flow
            account = stripe.Account.create(
                type="express",
                country="US",
                email=church.email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_type="non_profit",
                business_profile={
                    "name": church.name,
                    "url": church.website,
                    "mcc": "8661",  # Religious organizations
                },
                settings={
                    "payouts": {"schedule": {"delay_days": 2, "interval": "daily"}}
                },
            )

            # Validate account creation
            if not account or not account.id:

                raise Exception(
                    "Failed to create Stripe account - no account ID returned"
                )

            # Update church with Stripe account ID
            church.stripe_account_id = account.id
            church.kyc_state = "KYC_STARTED"
            church.updated_at = datetime.now(timezone.utc)

            # Commit church changes first
            db.commit()
            db.refresh(church)

            # Verify the account ID was saved in the database
            from app.model.m_church import Church

            saved_church = db.query(Church).filter(Church.id == church.id).first()
            if saved_church and saved_church.stripe_account_id:
                pass
            else:

                # Try to save it again
                church.stripe_account_id = account.id
                db.commit()
                db.refresh(church)

            # Log the action
            audit_log = AuditLog(
                actor_type="system",
                church_id=church.id,
                action="KYC_STARTED",
                details_json={
                    "stripe_account_id": account.id,
                    "previous_state": "REGISTERED",
                    "new_state": "KYC_STARTED",
                },
            )
            db.add(audit_log)
            db.commit()

            # Church object already refreshed above

            # Ensure we have the account ID even if database save failed
            account_id = account.id if account and account.id else None
            if not account_id:

                raise Exception("No Stripe account ID available")

            result_data = {"account_id": account_id, "kyc_state": church.kyc_state}

            return result_data

        except StripeError as e:
            raise StripeError(f"Failed to create Stripe account: {str(e)}")
        except Exception as e:
            raise StripeError(f"Failed to create Stripe account: {str(e)}")

    @staticmethod
    def submit_kyc_to_stripe(
        church: Church, beneficial_owners: List[BeneficialOwner], db: Session
    ) -> Dict[str, Any]:
        """Submit KYC data to Stripe Connect"""
        try:
            if not church.stripe_account_id:
                # Create Stripe account first
                account_result = KYCService.create_stripe_connect_account(church, db)
                # The account_id is already set in create_stripe_connect_account
                # Just refresh the church object to get the updated data
                db.refresh(church)

            else:
                pass

            # Validate required fields
            if not church.legal_name and not church.name:
                raise ValueError("Church legal name is required")
            if not church.ein:
                raise ValueError("Church EIN is required")
            if not beneficial_owners:
                raise ValueError("At least one beneficial owner is required")

            # Prepare company data for Stripe
            company_data = {
                "name": church.legal_name or church.name,
                "tax_id": church.ein,
                "address": {
                    "line1": church.address_line_1 or church.address,
                    "line2": church.address_line_2,
                    "city": church.city,
                    "state": church.state,
                    "postal_code": church.zip_code,
                    "country": church.country or "US",
                },
                "phone": church.phone,
                "website": church.website,
            }

            # Prepare individuals data (beneficial owners)
            individuals_data = []
            for owner in beneficial_owners:
                if not owner.first_name or not owner.last_name:
                    raise ValueError(
                        f"Beneficial owner {owner.id} missing required name fields"
                    )
                if not owner.email:
                    raise ValueError(f"Beneficial owner {owner.id} missing email")
                if not owner.date_of_birth:
                    raise ValueError(
                        f"Beneficial owner {owner.id} missing date of birth"
                    )

                individual = {
                    "first_name": owner.first_name,
                    "last_name": owner.last_name,
                    "email": owner.email,
                    "phone": owner.phone,
                    "address": {
                        "line1": owner.address_line_1,
                        "line2": owner.address_line_2,
                        "city": owner.city,
                        "state": owner.state,
                        "postal_code": owner.zip_code,
                        "country": owner.country,
                    },
                    "ssn_last_4": owner.ssn_full[-4:] if owner.ssn_full else None,
                    "dob": {
                        "day": owner.date_of_birth.day,
                        "month": owner.date_of_birth.month,
                        "year": owner.date_of_birth.year,
                    },
                    "verification": {
                        "document": {
                            "front": owner.gov_id_front,
                            "back": owner.gov_id_back,
                        }
                    },
                    "relationship": {
                        "title": owner.title,
                        "owner": True,
                        "executive": owner.is_primary,
                        "percent_ownership": 0,  # Not stored in current model
                    },
                }
                individuals_data.append(individual)

            # Update Stripe account with KYC data

            account = stripe.Account.modify(
                church.stripe_account_id,
                company=company_data,
                individuals=individuals_data,
                business_profile={
                    "name": church.legal_name or church.name,
                    "url": church.website,
                    "mcc": "8661",
                },
            )

            # Validate Stripe response

            if not account or not account.id:

                raise Exception("Invalid response from Stripe API")

            # Update KYC status
            church.kyc_status = "submitted"
            church.kyc_submitted_at = datetime.now(timezone.utc)
            church.kyc_state = "KYC_SUBMITTED"
            church.updated_at = datetime.now(timezone.utc)

            # Commit the church updates first
            db.commit()
            db.refresh(church)

            # Log the submission
            audit_log = AuditLog(
                actor_type="church_user",
                church_id=church.id,
                action="KYC_SUBMITTED",
                details_json={
                    "stripe_account_id": church.stripe_account_id,
                    "beneficial_owners_count": len(beneficial_owners),
                    "previous_state": "KYC_STARTED",
                    "new_state": "KYC_SUBMITTED",
                    "stripe_response": {
                        "account_id": account.id,
                        "status": getattr(account, "charges_enabled", None),
                        "payouts_enabled": getattr(account, "payouts_enabled", None),
                    },
                },
            )
            db.add(audit_log)
            db.commit()

            # Ensure we have the account ID from multiple sources
            account_id = (
                account.id if account and account.id else church.stripe_account_id
            )

            # Final validation - if we still don't have an account ID, something is wrong
            if not account_id:

                raise Exception("CRITICAL: No Stripe account ID available")

            result_data = {
                "account_id": account_id,
                "kyc_state": church.kyc_state,
                "status": church.kyc_status,
                "submitted_at": church.kyc_submitted_at,
                "stripe_account_status": {
                    "charges_enabled": getattr(account, "charges_enabled", False),
                    "payouts_enabled": getattr(account, "payouts_enabled", False),
                    "requirements": getattr(account, "requirements", {}),
                },
            }

            return result_data

        except Exception as e:
            # Rollback any database changes
            db.rollback()
            raise Exception(f"Stripe API error: {getattr(e, 'user_message', str(e))}")
        except ValueError as e:
            db.rollback()
            raise Exception(f"Validation error: {str(e)}")
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to submit KYC to Stripe: {str(e)}")

    @staticmethod
    def generate_onboarding_link(church: Church, db: Session) -> str:
        """Generate a fresh onboarding link for the church"""
        try:
            if not church.stripe_account_id:
                raise StripeError("No Stripe account found for church")

            # Create account link
            account_link = stripe.AccountLink.create(
                account=church.stripe_account_id,
                refresh_url=f"{config.ADMIN_FRONTEND_URL}/kyc/refresh",
                return_url=f"{config.ADMIN_FRONTEND_URL}/kyc/complete",
                type="account_onboarding",
                collect="eventually_due",
            )

            # Log the action
            audit_log = AuditLog(
                actor_type="church_user",
                church_id=church.id,
                action="ONBOARDING_LINK_GENERATED",
                details_json={
                    "stripe_account_id": church.stripe_account_id,
                    "link_url": account_link.url,
                },
            )
            db.add(audit_log)
            db.commit()

            return account_link.url

        except StripeError as e:
            raise StripeError(f"Failed to generate onboarding link: {str(e)}")
        except Exception as e:
            raise StripeError(f"Failed to generate onboarding link: {str(e)}")

    @staticmethod
    def sync_stripe_account_status(church: Church, db: Session) -> Dict[str, Any]:
        """Sync church status with Stripe account status"""
        try:
            if not church.stripe_account_id:
                return {"kyc_state": church.kyc_state}

            # Fetch account from Stripe
            account = stripe.Account.retrieve(church.stripe_account_id)

            # Determine next state based on Stripe account status
            next_state = KYCService._determine_kyc_state(account)

            # Update church if state changed
            if next_state != church.kyc_state:
                previous_state = church.kyc_state
                church.kyc_state = next_state
                church.charges_enabled = account.charges_enabled
                church.payouts_enabled = account.payouts_enabled
                church.disabled_reason = account.disabled_reason
                # Store requirements in kyc_data instead
                if church.kyc_data:
                    kyc_data = json.loads(church.kyc_data) if isinstance(church.kyc_data, str) else church.kyc_data
                else:
                    kyc_data = {}
                kyc_data['stripe_requirements'] = account.requirements
                church.kyc_data = json.dumps(kyc_data)
                church.updated_at = datetime.now(timezone.utc)

                # Set verified_at if becoming ACTIVE
                if next_state == "ACTIVE" and not church.verified_at:
                    church.verified_at = datetime.now(timezone.utc)

                # Log the state change
                audit_log = AuditLog(
                    actor_type="webhook",
                    church_id=church.id,
                    action="KYC_STATE_CHANGED",
                    details_json={
                        "previous_state": previous_state,
                        "new_state": next_state,
                        "charges_enabled": account.charges_enabled,
                        "payouts_enabled": account.payouts_enabled,
                        "disabled_reason": account.disabled_reason,
                    },
                )
                db.add(audit_log)
                db.commit()

            return {
                "kyc_state": church.kyc_state,
                "charges_enabled": church.charges_enabled,
                "payouts_enabled": church.payouts_enabled,
                "disabled_reason": church.disabled_reason,
            }

        except StripeError as e:
            raise StripeError(f"Failed to sync account status: {str(e)}")
        except Exception as e:
            raise StripeError(f"Failed to sync account status: {str(e)}")

    @staticmethod
    def _determine_kyc_state(account: stripe.Account) -> str:
        """Determine KYC state based on Stripe account status"""
        if account.disabled_reason:
            return "SUSPENDED"
        elif account.requirements and account.requirements.currently_due:
            return "KYC_NEEDS_INFO"
        elif account.charges_enabled and not account.payouts_enabled:
            return "VERIFIED"
        elif account.payouts_enabled:
            return "ACTIVE"
        else:
            return "KYC_IN_REVIEW"

    @staticmethod
    def pause_payouts(church: Church, db: Session, actor_id: int) -> Dict[str, Any]:
        """Pause payouts for a church"""
        try:
            if not church.stripe_account_id:
                raise StripeError("No Stripe account found for church")

            # Update account to disable payouts
            account = stripe.Account.modify(
                church.stripe_account_id,
                settings={"payouts": {"schedule": {"delay_days": 999}}},
            )

            # Update church status
            church.payouts_enabled = False
            church.updated_at = datetime.now(timezone.utc)

            # Log the action
            audit_log = AuditLog(
                actor_type="internal_admin",
                actor_id=actor_id,
                church_id=church.id,
                action="PAYOUTS_PAUSED",
                details_json={
                    "stripe_account_id": church.stripe_account_id,
                    "previous_payouts_enabled": True,
                },
            )
            db.add(audit_log)
            db.commit()

            return {"payouts_enabled": False}

        except StripeError as e:
            raise StripeError(f"Failed to pause payouts: {str(e)}")
        except Exception as e:
            raise StripeError(f"Failed to pause payouts: {str(e)}")

    @staticmethod
    def resume_payouts(church: Church, db: Session, actor_id: int) -> Dict[str, Any]:
        """Resume payouts for a church"""
        try:
            if not church.stripe_account_id:
                raise StripeError("No Stripe account found for church")

            # Update account to enable payouts
            account = stripe.Account.modify(
                church.stripe_account_id,
                settings={"payouts": {"schedule": {"delay_days": 2}}},
            )

            # Update church status
            church.payouts_enabled = True
            church.updated_at = datetime.now(timezone.utc)

            # Log the action
            audit_log = AuditLog(
                actor_type="internal_admin",
                actor_id=actor_id,
                church_id=church.id,
                action="PAYOUTS_RESUMED",
                details_json={
                    "stripe_account_id": church.stripe_account_id,
                    "previous_payouts_enabled": False,
                },
            )
            db.add(audit_log)
            db.commit()

            return {"payouts_enabled": True}

        except StripeError as e:
            raise StripeError(f"Failed to resume payouts: {str(e)}")
        except Exception as e:
            raise StripeError(f"Failed to resume payouts: {str(e)}")

    @staticmethod
    def validate_kyc_completeness(
        church: Church, beneficial_owners: List[BeneficialOwner]
    ) -> Dict[str, Any]:
        """Validate KYC application completeness"""
        errors = []
        warnings = []

        # Check required KYC fields
        if not church.legal_name and not church.name:
            errors.append("Legal name is required")
        if not church.ein:
            errors.append("EIN is required")
        if not church.phone:
            errors.append("Phone number is required")
        if not church.email:
            errors.append("Email is required")
        if not church.address_line_1 and not church.address:
            errors.append("Address is required")
        if not church.city:
            errors.append("City is required")
        if not church.state:
            errors.append("State is required")
        if not church.zip_code:
            errors.append("ZIP code is required")

        # Check required documents
        if not church.articles_of_incorporation_url:
            errors.append("Articles of Incorporation is required")
        if not church.irs_letter_url:
            errors.append("IRS Tax Exempt Letter is required")
        if not church.bank_statement_url:
            errors.append("Bank Statement is required")

        # Check beneficial owners
        if not beneficial_owners:
            errors.append("At least one beneficial owner is required")
        else:
            for i, owner in enumerate(beneficial_owners):
                if not owner.first_name or not owner.last_name:
                    errors.append(f"Beneficial owner {i+1}: Full name is required")
                if not owner.date_of_birth:
                    errors.append(f"Beneficial owner {i+1}: Date of birth is required")
                if not owner.ssn:
                    errors.append(f"Beneficial owner {i+1}: SSN is required")
                if not owner.email:
                    errors.append(f"Beneficial owner {i+1}: Email is required")
                if not owner.address_line_1:
                    errors.append(f"Beneficial owner {i+1}: Address is required")
                if not owner.id_front_url:
                    errors.append(f"Beneficial owner {i+1}: ID front image is required")

        # Check attestations
        if not church.tax_exempt:
            warnings.append("Tax exempt status should be confirmed")
        if not church.anti_terrorism:
            warnings.append("Anti-terrorism compliance should be confirmed")
        if not church.legitimate_entity:
            warnings.append("Legitimate entity attestation should be confirmed")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "completeness_percentage": max(0, 100 - (len(errors) * 10)),
        }
