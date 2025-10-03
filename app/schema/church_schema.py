"""
Church Management Schemas

Defines request and response schemas for church management endpoints:
- Church registration and onboarding
- KYC submission and verification
- Church dashboard and analytics
- Document upload handling
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


# ============================
# Request Schemas
# ============================

class ChurchAdminRegisterRequest(BaseModel):
    """Church admin registration request"""
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    role: Optional[str] = Field("admin", description="Admin role")

class ChurchAdminLoginRequest(BaseModel):
    """Church admin login request"""
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class ChurchProfileUpdateRequest(BaseModel):
    """Church profile update request"""
    name: Optional[str] = Field(None, description="Church name")
    description: Optional[str] = Field(None, description="Church description")
    website: Optional[str] = Field(None, description="Church website")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")
    address: Optional[str] = Field(None, description="Church address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country")

class ChurchRegistrationRequest(BaseModel):
    """Church registration request"""
    name: str = Field(..., description="Church name")
    email: str = Field(..., description="Admin email address")
    phone: str = Field(..., description="Contact phone number")
    address: str = Field(..., description="Church address")
    ein: str = Field(..., description="Tax ID (EIN)")
    website: Optional[str] = Field(None, description="Church website")
    description: Optional[str] = Field(None, description="Church description")

class ControlPersonRequest(BaseModel):
    """Control person information for KYC with full compliance requirements"""
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    title: str = Field(..., description="Title/position")
    is_primary: bool = Field(False, description="Is primary contact")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    ssn_full: str = Field(..., description="Full SSN")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    
    # Residential Address
    address: Dict[str, str] = Field(..., description="Residential address information")
    
    # Government ID Information
    gov_id_type: str = Field(..., description="Government-issued ID type (driver_license, passport, etc.)")
    gov_id_number: str = Field(..., description="Government-issued ID number")
    gov_id_front: Optional[str] = Field(None, description="Front of government ID file path")
    gov_id_back: Optional[str] = Field(None, description="Back of government ID file path")
    
    # Additional compliance fields
    country_of_citizenship: str = Field(..., description="Country of citizenship")
    country_of_residence: str = Field(..., description="Country of residence")

class ChurchKYCRequest(BaseModel):
    """Church KYC submission request with full compliance requirements"""
    # Step 1: Legal Information
    legal_name: str = Field(..., description="Legal entity name")
    ein: str = Field(..., description="Employer Identification Number")
    website: Optional[str] = Field(None, description="Organization website")
    phone: str = Field(..., description="Contact phone number")
    email: str = Field(..., description="Contact email address")
    address: str = Field(..., description="Business address (will be stored as address_line_1)")
    address_line_2: Optional[str] = Field(None, description="Business address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="ZIP code")
    country: str = Field(..., description="Country")
    primary_purpose: Optional[str] = Field(None, description="Primary business purpose")
    formation_date: Optional[str] = Field(None, description="Date of formation (YYYY-MM-DD)")
    formation_state: Optional[str] = Field(None, description="State of formation")
    
    # Step 2: Beneficial Owners & Control Persons
    control_persons: List[ControlPersonRequest] = Field(..., description="List of control persons")
    
    # Step 3: Required Documents
    articles_of_incorporation: Optional[str] = Field(None, description="Articles of Incorporation file path")
    tax_exempt_letter: Optional[str] = Field(None, description="501(c)(3) Tax-Exempt Determination Letter file path")
    bank_statement: Optional[str] = Field(None, description="Recent Bank Statement file path")
    board_resolution: Optional[str] = Field(None, description="Board Resolution file path")
    
    # Required Compliance Attestations
    tax_exempt: bool = Field(False, description="Tax exempt status attestation")
    anti_terrorism: bool = Field(False, description="Anti-terrorism compliance attestation")
    legitimate_entity: bool = Field(False, description="Legitimate entity attestation")
    consent_checks: bool = Field(False, description="Consent for background checks")
    beneficial_ownership_disclosure: bool = Field(False, description="Beneficial ownership disclosure")
    information_accuracy: bool = Field(False, description="Information accuracy attestation")
    penalty_of_perjury: bool = Field(False, description="Penalty of perjury attestation")

class ChurchOnboardingRequest(BaseModel):
    """Combined church onboarding request (profile + KYC) with comprehensive compliance requirements"""
    # Church profile information
    name: str = Field(..., description="Church name")
    legal_name: str = Field(..., description="Legal business name")
    ein: str = Field(..., description="EIN (Tax ID)")
    denomination: Optional[str] = Field(None, description="Denomination")
    address: str = Field(..., description="Church address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    pastor_name: Optional[str] = Field(None, description="Pastor name")
    phone: str = Field(..., description="Phone number")
    contact_email: str = Field(..., description="Contact email")
    website: Optional[str] = Field(None, description="Website")
    congregation_size: str = Field(..., description="Congregation size")
    primary_purpose: Optional[str] = Field(None, description="Primary business purpose")
    referral_code: Optional[str] = Field(None, description="Referral code if referred by another church")
    
    # Church admin information
    admin_password: str = Field(..., description="Church admin password")
    admin_first_name: str = Field(..., description="Church admin first name")
    admin_last_name: str = Field(..., description="Church admin last name")
    admin_title: str = Field(..., description="Church admin title")
    admin_phone: str = Field(..., description="Church admin phone number")
    
    # Comprehensive KYC information with all required compliance fields
    control_persons: List[ControlPersonRequest] = Field(..., description="List of control persons/UBOs")
    
    # Required Documents (file paths after upload)
    articles_of_incorporation: Optional[str] = Field(None, description="Articles of Incorporation file path")
    tax_exempt_letter: Optional[str] = Field(None, description="501(c)(3) Tax-Exempt Determination Letter file path")
    bank_statement: Optional[str] = Field(None, description="Recent Bank Statement file path")
    board_resolution: Optional[str] = Field(None, description="Board Resolution file path")
    
    # Required Compliance Attestations
    tax_exempt: bool = Field(False, description="Tax exempt status attestation")
    anti_terrorism: bool = Field(False, description="Anti-terrorism compliance attestation")
    legitimate_entity: bool = Field(False, description="Legitimate entity attestation")
    consent_checks: bool = Field(False, description="Consent for background checks")
    beneficial_ownership_disclosure: bool = Field(False, description="Beneficial ownership disclosure")
    information_accuracy: bool = Field(False, description="Information accuracy attestation")
    penalty_of_perjury: bool = Field(False, description="Penalty of perjury attestation")
    
    # Additional KYC data from frontend (for reference)
    kyc_data: Optional[Dict[str, Any]] = Field(None, description="Complete KYC data from frontend for reference")

class BeneficialOwnerRequest(BaseModel):
    """Beneficial owner submission request"""
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    ssn: str = Field(..., description="Social Security Number")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address_line_1: str = Field(..., description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="ZIP code")
    country: str = Field(..., description="Country")
    id_type: str = Field(..., description="ID type (driver_license, passport, state_id)")
    id_number: str = Field(..., description="ID number")
    id_issuing_country: str = Field(..., description="ID issuing country")
    id_expiration_date: Optional[str] = Field(None, description="ID expiration date (YYYY-MM-DD)")
    ownership_percentage: Optional[int] = Field(None, description="Ownership percentage")
    title: Optional[str] = Field(None, description="Title/position")
    is_control_person: bool = Field(False, description="Is control person")

class BeneficialOwnerUpdateRequest(BaseModel):
    """Beneficial owner update request"""
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    ssn: Optional[str] = Field(None, description="Social Security Number")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address_line_1: Optional[str] = Field(None, description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country")
    id_type: Optional[str] = Field(None, description="ID type")
    id_number: Optional[str] = Field(None, description="ID number")
    id_issuing_country: Optional[str] = Field(None, description="ID issuing country")
    id_expiration_date: Optional[str] = Field(None, description="ID expiration date (YYYY-MM-DD)")
    ownership_percentage: Optional[int] = Field(None, description="Ownership percentage")
    title: Optional[str] = Field(None, description="Title/position")
    is_control_person: Optional[bool] = Field(None, description="Is control person")

class KYCUpdateRequest(BaseModel):
    """KYC information update request"""
    legal_name: Optional[str] = Field(None, description="Legal entity name")
    ein: Optional[str] = Field(None, description="Employer Identification Number")
    website: Optional[str] = Field(None, description="Organization website")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    address: Optional[str] = Field(None, description="Business address")
    address_line_2: Optional[str] = Field(None, description="Business address line 2")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country")
    tax_exempt: Optional[bool] = Field(None, description="Tax exempt status")
    anti_terrorism: Optional[bool] = Field(None, description="Anti-terrorism compliance")
    legitimate_entity: Optional[bool] = Field(None, description="Legitimate entity attestation")
    consent_checks: Optional[bool] = Field(None, description="Consent to background checks")
    ownership_disclosed: Optional[bool] = Field(None, description="Ownership disclosure")
    info_accurate: Optional[bool] = Field(None, description="Information accuracy attestation")

# Add missing schemas for mobile endpoints
class ChurchSearchRequest(BaseModel):
    """Church search request"""
    query: str = Field(..., description="Search query for church name or location")


class ChurchUpdateRequest(BaseModel):
    """Church update request"""
    name: Optional[str] = Field(None, description="Church name")
    description: Optional[str] = Field(None, description="Church description")
    website: Optional[str] = Field(None, description="Church website")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")
    address: Optional[str] = Field(None, description="Church address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country")
    logo_url: Optional[str] = Field(None, description="Church logo URL")


# ============================
# Response Schemas
# ============================

class BeneficialOwnerResponse(BaseModel):
    """Beneficial owner response"""
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str]
    full_name: str
    date_of_birth: Optional[str]
    ssn: str
    email: str
    phone: Optional[str]
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    zip_code: str
    country: str
    id_type: str
    id_number: str
    id_issuing_country: str
    id_expiration_date: Optional[str]
    id_front_url: Optional[str]
    id_back_url: Optional[str]
    ownership_percentage: Optional[int]
    title: Optional[str]
    is_control_person: bool
    is_verified: bool
    verified_at: Optional[str]
    created_at: str
    updated_at: str

class KYCStatusResponse(BaseModel):
    """KYC status response"""
    status: str
    submitted_at: Optional[str]
    updated_at: Optional[str]
    legal_name: Optional[str]
    ein: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    documents: dict
    attestations: dict
    beneficial_owners: List[BeneficialOwnerResponse]
    total_owners: int
    validation: dict
    kyc_state: Optional[str]
    stripe_account_id: Optional[str]

class KYCValidationResponse(BaseModel):
    """KYC validation response"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    completeness_percentage: int

class DocumentResponse(BaseModel):
    """Document response"""
    url: Optional[str]
    uploaded: bool

class DocumentsResponse(BaseModel):
    """Documents response"""
    documents: dict
    total_uploaded: int
    total_required: int

class BeneficialOwnersResponse(BaseModel):
    """Beneficial owners response"""
    owners: List[BeneficialOwnerResponse]
    total_owners: int

class ChurchAdminData(BaseModel):
    """
    Church admin data for API responses.
    Represents a church admin with identity verification fields.
    """
    id: int = Field(..., description="Unique church admin ID")
    user_id: int = Field(..., description="User ID for the church admin")
    church_id: int = Field(..., description="Church ID for the admin")
    admin_name: Optional[str] = Field(None, description="Display name for the admin")
    role: str = Field(..., description="Admin role (admin, moderator, treasurer, etc.)")
    is_active: bool = Field(..., description="Whether the admin is active")
    is_primary_admin: bool = Field(..., description="Whether this is the primary admin")
    can_manage_finances: bool = Field(..., description="Whether admin can manage finances")
    can_manage_members: bool = Field(..., description="Whether admin can manage members")
    can_manage_settings: bool = Field(..., description="Whether admin can manage settings")
    contact_email: Optional[str] = Field(None, description="Admin contact email")
    contact_phone: Optional[str] = Field(None, description="Admin contact phone")
    
    # Identity verification fields (KYC for payouts)
    stripe_identity_session_id: Optional[str] = Field(None, description="Stripe Identity session ID")
    identity_verification_status: str = Field(..., description="Identity verification status")
    identity_verification_date: Optional[datetime] = Field(None, description="Identity verification completion date")
    
    created_at: datetime = Field(..., description="Timestamp when the admin was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the admin was last updated")
    last_activity: Optional[datetime] = Field(None, description="Timestamp of last admin activity")

    class Config:
        from_attributes = True
