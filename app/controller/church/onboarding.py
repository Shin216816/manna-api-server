"""
New Church Onboarding Controller

Handles the new church onboarding flow:
- Combined church profile + KYC submission
- Stripe Connect account creation
- Beneficial owner management
"""

from sqlalchemy.orm import Session
from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_church_admin import ChurchAdmin
from app.model.m_beneficial_owner import BeneficialOwner
from app.model.m_church_referral import ChurchReferral
from app.schema.church_schema import ChurchOnboardingRequest
from app.core.responses import ResponseFactory
from app.utils.audit import log_audit_event
from app.utils.encryption import hash_password
from app.utils.business_validation import normalize_ein, normalize_ssn
from app.services.stripe_service import create_connect_account, create_account_link
from app.config import config
from datetime import datetime, timezone
import logging
import json
import uuid


def get_frontend_url(config):
    """Get the appropriate frontend URL based on environment"""
    if config.IS_DEVELOPMENT:
        return "http://localhost:3000"
    return config.ADMIN_FRONTEND_URL


def submit_church_onboarding(data: ChurchOnboardingRequest, db: Session):
    """Submit combined church profile and KYC information, create Stripe Connect account"""
    try:
        logging.info(f"Starting church onboarding submission for: {data.name}")
        logging.info(f"Data received: {data.dict()}")

        # Normalize EIN for comparison
        normalized_ein = normalize_ein(data.ein)
        
        # Check if church with same EIN already exists
        if normalized_ein:
            existing_churches = db.query(Church).filter(Church.ein.isnot(None)).all()
            for church in existing_churches:
                existing_normalized = normalize_ein(church.ein)
                if existing_normalized == normalized_ein:
                    logging.warning(f"Church with EIN {data.ein} (normalized: {normalized_ein}) already exists as church ID {church.id}")
                    return ResponseFactory.error(
                        message=f"A church with EIN {data.ein} already exists. Each church must have a unique EIN.",
                        error_code="DUPLICATE_EIN"
                    )

        # Check if admin email already exists
        existing_admin = db.query(User).filter_by(email=data.contact_email).first()
        if existing_admin:
            logging.warning(f"Admin email {data.contact_email} already registered")
            return ResponseFactory.error(
                message="This email address is already registered. Please use a different email or contact support if this is your account.",
                error_code="DUPLICATE_EMAIL"
            )

        # Check if admin phone already exists
        existing_phone = db.query(User).filter_by(phone=data.admin_phone).first()
        if existing_phone:
            logging.warning(f"Admin phone {data.admin_phone} already registered")
            return ResponseFactory.error(
                message="This phone number is already registered. Please use a different phone number or contact support if this is your account.",
                error_code="DUPLICATE_PHONE"
            )

        # Handle referral code if provided
        referral_relationship = None
        if data.referral_code:
            logging.info(f"Processing referral code: {data.referral_code}")
            try:
                # Find the referral code
                referral = db.query(ChurchReferral).filter(
                    ChurchReferral.referral_code == data.referral_code,
                    ChurchReferral.status == "active"
                ).first()
                
                if referral:
                    # Check if referral code is expired
                    if referral.expires_at and referral.expires_at < datetime.now(timezone.utc):
                        logging.warning(f"Referral code {data.referral_code} has expired")
                    else:
                        # Check if church is trying to use their own referral code
                        if referral.referring_church_id:
                            # We'll update this after creating the church
                            referral_relationship = referral
                            logging.info(f"Valid referral code found: {data.referral_code}")
                        else:
                            logging.warning(f"Referral code {data.referral_code} has no referring church")
                else:
                    logging.warning(f"Referral code {data.referral_code} not found or inactive")
            except Exception as e:
                logging.error(f"Error processing referral code: {str(e)}")

        # Create church record with complete information
        logging.info("Creating church record...")
        church = Church(
            name=data.name,
            legal_name=data.legal_name,
            ein=data.ein,
            website=data.website,
            phone=data.phone,
            address=data.address,
            address_line_1=data.address,
            city=data.city,
            state=data.state,
            zip_code=data.zip_code,
            country="US",
            email=data.contact_email,
            pastor_name=data.pastor_name,
            primary_purpose=data.primary_purpose or "",
            kyc_status="pending_review",
            kyc_submitted_at=datetime.now(timezone.utc),
            status="pending_kyc",
            kyc_state="KYC_IN_REVIEW",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Store KYC data as JSON (including denomination and congregation_size)
        logging.info("Storing KYC data...")
        kyc_data_with_church_info = data.kyc_data.copy() if data.kyc_data else {}
        
        # Add church profile data to KYC JSON since these fields aren't in the DB schema
        kyc_data_with_church_info.update({
            "denomination": data.denomination,
            "congregation_size": data.congregation_size
        })
        
        kyc_json = json.dumps(kyc_data_with_church_info)
        church.kyc_data = kyc_json

        # Set attestation flags (use top-level fields)
        church.tax_exempt = data.tax_exempt
        church.anti_terrorism = data.anti_terrorism
        church.legitimate_entity = data.legitimate_entity
        church.consent_checks = data.consent_checks
        church.beneficial_ownership_disclosure = data.beneficial_ownership_disclosure
        church.information_accuracy = data.information_accuracy
        church.penalty_of_perjury = data.penalty_of_perjury

        logging.info("Adding church to database...")
        db.add(church)
        db.flush()  # Get the church ID
        logging.info(f"Church created with ID: {church.id}")

        # Create admin user with proper admin information
        logging.info("Creating admin user...")
        admin_user = User(
            email=data.contact_email,
            password_hash=hash_password(data.admin_password),
            first_name=data.admin_first_name,
            last_name=data.admin_last_name,
            phone=data.admin_phone,
            role="church_admin",
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(admin_user)
        db.flush()  # Get the user ID
        logging.info(f"Admin user created with ID: {admin_user.id}")

        # Create church admin record with complete admin information
        logging.info("Creating church admin record...")
        church_admin = ChurchAdmin(
            user_id=admin_user.id, 
            church_id=church.id,
            admin_name=f"{data.admin_first_name} {data.admin_last_name}",
            role="church_admin",
            is_active=True,
            is_primary_admin=True,
            can_manage_finances=True,
            can_manage_members=True,
            can_manage_settings=True,
            contact_email=data.contact_email,
            contact_phone=data.admin_phone,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(church_admin)
        logging.info("Church admin record created")

        # Create beneficial owners from control persons data (top-level field)
        logging.info("Creating beneficial owners...")
        control_persons = data.control_persons if hasattr(data, 'control_persons') else []
        logging.info(f"Found {len(control_persons)} control persons")
        
        for i, person_data in enumerate(control_persons):
            try:
                logging.info(f"Processing control person {i+1}: {person_data.first_name} {person_data.last_name}")
                beneficial_owner = BeneficialOwner(
                    church_id=church.id,
                    first_name=person_data.first_name,
                    last_name=person_data.last_name,
                    date_of_birth=datetime.strptime(
                        person_data.date_of_birth, "%Y-%m-%d"
                    ).date(),
                    ssn_full=normalize_ssn(person_data.ssn_full) or "",
                    email=person_data.email,
                    phone=person_data.phone,
                    address_line_1=person_data.address.get("line1", "") if person_data.address else "",
                    city=person_data.address.get("city", "") if person_data.address else "",
                    state=person_data.address.get("state", "") if person_data.address else "",
                    zip_code=person_data.address.get("postal_code", "") if person_data.address else "",
                    country="US",
                    gov_id_type=person_data.gov_id_type,
                    gov_id_number=person_data.gov_id_number,
                    country_of_citizenship=person_data.country_of_citizenship,
                    country_of_residence=person_data.country_of_residence,
                    title=person_data.title,
                    is_primary=person_data.is_primary,
                )
                db.add(beneficial_owner)
                logging.info(f"Beneficial owner {i+1} added successfully")
            except Exception as bo_error:
                logging.error(f"Error creating beneficial owner {i+1}: {str(bo_error)}")
                raise bo_error

        # Create Stripe Connect account
        logging.info(f"Creating Stripe Connect account for church: {church.name}")
        logging.info(f"Environment: {config.ENVIRONMENT}, Development mode: {config.IS_DEVELOPMENT}")
        logging.info(f"Configured ADMIN_FRONTEND_URL: {config.ADMIN_FRONTEND_URL}")
        try:
            stripe_account = create_connect_account(
                type="express",
                country="US",
                email=data.contact_email,
                business_type="non_profit",
            )

            church.stripe_account_id = stripe_account.get("id")
            church.charges_enabled = stripe_account.get("charges_enabled", False)
            church.payouts_enabled = stripe_account.get("payouts_enabled", False)
            logging.info(f"Stripe account created successfully: {stripe_account.get('id')}")
            logging.info(f"Account status: charges_enabled={stripe_account.get('charges_enabled')}, payouts_enabled={stripe_account.get('payouts_enabled')}")

            # Create account link for onboarding - use localhost for development
            try:
                # Determine frontend URL based on environment
                frontend_url = get_frontend_url(config)
                logging.info(f"Using frontend URL for Stripe redirects: {frontend_url}")
                logging.info(f"Environment check - IS_DEVELOPMENT: {config.IS_DEVELOPMENT}, ENVIRONMENT: {config.ENVIRONMENT}")
                
                refresh_url = f"{frontend_url}/church/onboarding/stripe/refresh"
                return_url = f"{frontend_url}/church/onboarding/complete"
                
                logging.info(f"Creating account link with refresh_url: {refresh_url}")
                logging.info(f"Creating account link with return_url: {return_url}")
                
                account_link = create_account_link(
                    stripe_account.get("id"),
                    refresh_url=refresh_url,
                    return_url=return_url
                )
                
                logging.info(f"Account link created successfully: {account_link.get('url')}")
                
            except Exception as link_error:
                logging.error(f"Failed to create account link: {str(link_error)}")
                logging.error(f"Link error type: {type(link_error)}")
                account_link = {"url": None, "error": str(link_error)}

            stripe_data = {
                "account_id": stripe_account.get("id"),
                "account_link": account_link.get("url"),
                "charges_enabled": stripe_account.get("charges_enabled", False),
                "payouts_enabled": stripe_account.get("payouts_enabled", False),
                "requirements": stripe_account.get("requirements", {}),
                "details_submitted": stripe_account.get("details_submitted", False),
                "currently_due": stripe_account.get("requirements", {}).get("currently_due", []),
                "eventually_due": stripe_account.get("requirements", {}).get("eventually_due", []),
                "capabilities": stripe_account.get("capabilities", {}),
                "business_type": stripe_account.get("business_type"),
                "country": stripe_account.get("country"),
                "type": stripe_account.get("type"),
            }

        except Exception as stripe_error:
            logging.error(f"Stripe account creation failed: {str(stripe_error)}")
            logging.error(f"Stripe error type: {type(stripe_error)}")
            logging.warning("Continuing without Stripe account - can be created later")
            # Continue without Stripe account - it can be created later
            stripe_data = {
                "account_id": None,
                "account_link": None,
                "charges_enabled": False,
                "payouts_enabled": False,
                "requirements": {},
                "error": str(stripe_error),
                "error_type": str(type(stripe_error)),
            }

        db.commit()

        # Update referral relationship if referral code was provided
        if referral_relationship:
            try:
                logging.info(f"Updating referral relationship for church {church.id}")
                referral_relationship.referred_church_id = church.id
                referral_relationship.updated_at = datetime.now(timezone.utc)
                db.commit()
                logging.info(f"Referral relationship updated successfully: {referral_relationship.referring_church_id} -> {church.id}")
            except Exception as e:
                logging.error(f"Error updating referral relationship: {str(e)}")
                # Don't fail the onboarding if referral update fails

        # Log audit event
        log_audit_event(
            db=db,
            actor_type="system",
            actor_id=0,
            action="CHURCH_ONBOARDING_SUBMITTED",
            metadata={
                "resource_type": "church",
                "resource_id": church.id,
                "church_name": church.name,
                "admin_email": data.contact_email,
                "kyc_status": "pending_review",
                "stripe_account_created": stripe_data.get("account_id") is not None,
            },
        )

        response_data = {
            "church_id": church.id,
            "admin_id": admin_user.id,
            "kyc_status": "pending_review",
            "stripe_data": stripe_data,
            "next_step": "stripe_onboarding",
        }

        return ResponseFactory.success(
            message="Church onboarding submitted successfully", data=response_data
        )

    except Exception as e:
        logging.error(f"Church onboarding submission error: {str(e)}", exc_info=True)
        db.rollback()
        return ResponseFactory.error(f"Error submitting church onboarding: {str(e)}", "500")


def get_church_onboarding_status(church_id: int, db: Session):
    """Get church onboarding status including KYC and Stripe status"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")

        # Parse KYC data
        kyc_data = {}
        if church.kyc_data:
            try:
                kyc_data = json.loads(church.kyc_data)
            except json.JSONDecodeError:
                kyc_data = {}

        # Get Stripe account status if exists
        stripe_status = {}
        if church.stripe_account_id:
            try:
                from app.services.stripe_service import get_account

                stripe_account = get_account(church.stripe_account_id)
                stripe_status = {
                    "account_id": stripe_account.get("id"),
                    "charges_enabled": stripe_account.get("charges_enabled", False),
                    "payouts_enabled": stripe_account.get("payouts_enabled", False),
                    "requirements": stripe_account.get("requirements", {}),
                    "verification": stripe_account.get("verification", {}),
                }
            except Exception as e:

                stripe_status = {"error": str(e)}

        return ResponseFactory.success(
            message="Onboarding status retrieved successfully",
            data={
                "church_id": church.id,
                "church_name": church.name,
                "kyc_status": church.kyc_status,
                "kyc_state": church.kyc_state,
                "stripe_status": stripe_status,
                "is_active": church.is_active,
                "created_at": (
                    church.created_at.isoformat() if church.created_at else None
                ),
            },
        )

    except Exception as e:

        return ResponseFactory.error("Error retrieving onboarding status", "500")


def update_stripe_onboarding_status(church_id: int, stripe_data: dict, db: Session):
    """Update Stripe onboarding status after completion"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")

        # Get current Stripe account status
        current_stripe_status = {}
        if church.stripe_account_id:
            try:
                from app.services.stripe_service import get_account

                stripe_account = get_account(church.stripe_account_id)
                current_stripe_status = {
                    "account_id": stripe_account.get("id"),
                    "charges_enabled": stripe_account.get("charges_enabled", False),
                    "payouts_enabled": stripe_account.get("payouts_enabled", False),
                    "requirements": stripe_account.get("requirements", {}),
                    "verification": stripe_account.get("verification", {}),
                }

                # Update church fields with current Stripe status
                church.charges_enabled = current_stripe_status["charges_enabled"]
                church.payouts_enabled = current_stripe_status["payouts_enabled"]
                # Store requirements in kyc_data instead
                if church.kyc_data:
                    kyc_data = json.loads(church.kyc_data) if isinstance(church.kyc_data, str) else church.kyc_data
                else:
                    kyc_data = {}
                kyc_data['stripe_requirements'] = current_stripe_status["requirements"]
                church.kyc_data = json.dumps(kyc_data)

                # Update church status if Stripe onboarding is complete
                if (
                    current_stripe_status["charges_enabled"]
                    and current_stripe_status["payouts_enabled"]
                ):
                    church.status = "active"
                    church.kyc_state = "ACTIVE"
                    church.is_active = True

                db.commit()

                # Log audit event
                log_audit_event(
                    db=db,
                    actor_type="church_admin",
                    actor_id=church_id,
                    action="STRIPE_ONBOARDING_UPDATED",
                    metadata={
                        "resource_type": "church",
                        "resource_id": church_id,
                        "charges_enabled": current_stripe_status["charges_enabled"],
                        "payouts_enabled": current_stripe_status["payouts_enabled"],
                    },
                )

                return ResponseFactory.success(
                    message="Stripe onboarding status updated successfully",
                    data={
                        "church_id": church.id,
                        "stripe_status": current_stripe_status,
                        "church_status": church.status,
                    },
                )

            except Exception as stripe_error:

                return ResponseFactory.error(
                    f"Error checking Stripe status: {str(stripe_error)}", "500"
                )
        else:
            return ResponseFactory.error(
                "No Stripe account found for this church", "404"
            )

    except Exception as e:

        db.rollback()
        return ResponseFactory.error("Error updating Stripe onboarding status", "500")


def complete_church_onboarding(church_id: int, db: Session):
    """Complete church onboarding and generate auth token"""
    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            return ResponseFactory.error("Church not found", "404")

        # Get the church admin
        church_admin = db.query(ChurchAdmin).filter_by(church_id=church_id).first()
        if not church_admin:
            return ResponseFactory.error("Church admin not found", "404")

        admin_user = db.query(User).filter_by(id=church_admin.user_id).first()
        if not admin_user:
            return ResponseFactory.error("Admin user not found", "404")

        # Check if Stripe onboarding is complete
        if not church.charges_enabled or not church.payouts_enabled:
            return ResponseFactory.error(
                "Stripe onboarding must be completed first", "400"
            )

        # Generate JWT token for the admin user
        from app.utils.token_manager import token_manager
        from app.services.session_service import session_manager

        # Ensure the user record is committed before token generation
        db.commit()
        db.refresh(admin_user)
        
        # Verify user exists and has correct role
        if admin_user.role != "church_admin":
            return ResponseFactory.error("Admin user role not set correctly", "500")

        access_token, jti, session_id = token_manager.create_access_token(
            data={
                "id": admin_user.id,
                "user_id": admin_user.id,
                "sub": str(admin_user.id),
                "role": "church_admin",
                "church_id": church.id,
            }
        )

        # Manually create session since we don't have request context
        if not session_id:
            try:
                session_id = session_manager.create_session(
                    user_id=admin_user.id,
                    user_type="church_admin",
                    church_id=church.id,
                    device_info={"type": "web", "name": "Church Admin Onboarding"},
                    ip_address="127.0.0.1",  # Default for onboarding
                    user_agent="Manna Church Admin Onboarding",
                    access_token_jti=jti,
                )

                # Update the JWT token to include session_id
                if session_id:
                    # Recreate token with session_id
                    token_data = {
                        "id": admin_user.id,
                        "user_id": admin_user.id,
                        "sub": str(admin_user.id),
                        "role": "church_admin",
                        "church_id": church.id,
                        "session_id": session_id,
                    }
                    access_token, jti, _ = token_manager.create_access_token(
                        data=token_data
                    )
            except Exception as session_error:

                session_id = None

        # Update church status to active
        church.status = "active"
        church.is_active = True
        church.kyc_state = "ACTIVE"
        db.commit()

        # Log audit event
        log_audit_event(
            db=db,
            actor_type="system",
            actor_id=0,
            action="CHURCH_ONBOARDING_COMPLETED",
            metadata={
                "resource_type": "church",
                "resource_id": church_id,
                "church_name": church.name,
                "admin_email": admin_user.email,
            },
        )

        return ResponseFactory.success(
            message="Church onboarding completed successfully",
            data={
                "church_id": church.id,
                "admin_id": admin_user.id,
                "auth_token": access_token,
                "session_id": session_id,
                "user": {
                    "id": admin_user.id,
                    "email": admin_user.email,
                    "first_name": admin_user.first_name,
                    "last_name": admin_user.last_name,
                    "role": admin_user.role,
                },
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "status": church.status,
                },
            },
        )

    except Exception as e:

        db.rollback()
        return ResponseFactory.error("Error completing church onboarding", "500")
