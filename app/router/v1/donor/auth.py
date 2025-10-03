from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.controller.donor.auth import donor_signup, donor_login, donor_register, donor_forgot_password, donor_verify_otp, donor_reset_password, donor_confirm_registration, donor_resend_registration_code, donor_change_password, donor_send_phone_verification, donor_verify_phone_verification, donor_set_password, donor_verify_reset_password_otp
from app.schema.donor_schema import DonorSignupRequest, DonorLoginRequest, DonorGoogleOAuthRequest, DonorRegisterRequest, DonorForgotPasswordRequest, DonorVerifyOtpRequest, DonorResetPasswordRequest, DonorRegisterConfirmRequest, DonorRegisterCodeResendRequest, DonorChangePasswordRequest, DonorSendPhoneVerificationRequest, DonorVerifyPhoneVerificationRequest
from app.schema.auth_schema import AppleOAuthRequest
from app.core.responses import SuccessResponse
from app.services.oauth_service import donor_google_oauth_service
from app.controller.auth.apple_oauth import apple_oauth_login
from app.middleware.auth_middleware import get_current_user

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=SuccessResponse)
def register(data: DonorRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new donor account
    
    Creates a new donor account with the provided church ID and user information.
    This endpoint is used for direct registration without an invite token.
    """
    return donor_register(
        db=db,
        user_data=data.dict()
    )

@router.post("/signup", response_model=SuccessResponse)
def signup(data: DonorSignupRequest, request: Request, db: Session = Depends(get_db)):
    """
    Sign up with invite token
    
    Creates a new donor account using an invite token from a church.
    This is the primary registration method for donors.
    """
    return donor_signup(
        db=db,
        email=data.email,
        password=data.password,
        oauth_provider=data.oauth_provider,
        invite_token=data.invite_token,
        first_name=data.first_name,
        last_name=data.last_name,
        request=request
    )

@router.post("/login", response_model=SuccessResponse)
def login(data: DonorLoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Login donor account
    
    Authenticates a donor with email and password, returning an access token
    for subsequent API requests.
    """
    return donor_login(
        db=db,
        email=data.email,
        password=data.password,
        oauth_provider=data.oauth_provider,
        request=request
    )

@router.post("/google-oauth", response_model=SuccessResponse)
def google_oauth(data: DonorGoogleOAuthRequest, db: Session = Depends(get_db)):
    """
    Google OAuth authentication
    
    Authenticates or creates a donor account using Google OAuth.
    Requires a valid Google ID token.
    """
    return donor_google_oauth_service.authenticate_or_create_donor_temp(
        id_token_string=data.id_token,
        db=db
    )

@router.post("/apple-oauth", response_model=SuccessResponse)
def apple_oauth(data: AppleOAuthRequest, db: Session = Depends(get_db)):
    """
    Apple OAuth authentication
    
    Authenticates or creates a donor account using Apple OAuth.
    Requires a valid Apple ID token.
    """
    return apple_oauth_login(data, db)

@router.post("/forgot-password", response_model=SuccessResponse)
def forgot_password(data: DonorForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset
    
    Sends password reset instructions to the donor's email address.
    An OTP will be sent for verification.
    """
    return donor_forgot_password(data, db)

@router.post("/verify-otp", response_model=SuccessResponse)
def verify_otp(data: DonorVerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Verify OTP code
    
    Verifies the OTP code sent to the donor's email for password reset.
    Must be called before resetting the password.
    """
    return donor_verify_otp(data, db)

@router.post("/reset-password", response_model=SuccessResponse)
def reset_password(data: DonorResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password
    
    Resets the donor's password using a verified OTP code.
    The OTP must be verified first using the verify-otp endpoint.
    """
    return donor_reset_password(data, db)

@router.post("/register/confirm", response_model=SuccessResponse)
def confirm_registration(data: DonorRegisterConfirmRequest, db: Session = Depends(get_db)):
    """
    Confirm registration
    
    Confirms donor registration using the OTP code sent to their email.
    Required to activate the account after registration.
    """
    return donor_confirm_registration(data, db)

@router.post("/register/resend-code", response_model=SuccessResponse)
def resend_registration_code(data: DonorRegisterCodeResendRequest, db: Session = Depends(get_db)):
    """
    Resend registration code
    
    Resends the registration OTP code to the donor's email address.
    Useful if the original code was not received or expired.
    """
    return donor_resend_registration_code(data, db)

@router.post("/change-password", response_model=SuccessResponse)
def change_password(data: DonorChangePasswordRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Change password
    
    Changes the donor's password. Requires authentication.
    The current password must be provided for verification.
    """
    return donor_change_password(data, current_user["user_id"], db)

@router.post("/send-phone-verification", response_model=SuccessResponse)
def send_phone_verification(data: DonorSendPhoneVerificationRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Send phone verification code
    
    Sends an OTP verification code to the donor's phone number.
    Requires authentication.
    """
    return donor_send_phone_verification(data.phone, current_user["user_id"], db)

@router.post("/verify-phone-verification", response_model=SuccessResponse)
def verify_phone_verification(data: DonorVerifyPhoneVerificationRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verify phone number
    
    Verifies the donor's phone number using the OTP code sent to their phone.
    Requires authentication.
    """
    return donor_verify_phone_verification(data.phone, data.access_code, current_user["user_id"], db)

@router.post("/set-password", response_model=SuccessResponse)
def set_password(data: DonorChangePasswordRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Set initial password
    
    Sets the initial password for OAuth users who don't have a password yet.
    Requires authentication.
    """
    return donor_set_password(data, current_user["user_id"], db)

@router.post("/verify-reset-password-otp", response_model=SuccessResponse)
def verify_reset_password_otp(data: DonorVerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Verify reset password OTP
    
    Verifies the OTP code for password reset and deletes the user's password.
    After successful verification, the user can set a new password.
    """
    return donor_verify_reset_password_otp(data, db)
