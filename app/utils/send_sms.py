# app/utils/send_sms.py
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app.config import config
from typing import Optional

def send_sms_with_twilio(to_phone: str, message: str, from_phone: Optional[str] = None):
    """
    Send SMS using Twilio with API key authentication
    Sends actual SMS in both development and production environments
    """
    try:
        # Validate required configuration
        if not config.TWILIO_ACCOUNT_SID:
            return False
            
        if not config.TWILIO_AUTH_TOKEN:
            return False
            
        if not config.TWILIO_PHONE_NUMBER:
            return False

        # Use provided from_phone or default from config
        from_phone = from_phone or config.TWILIO_PHONE_NUMBER
        
        # Create Twilio client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Send SMS
        message_obj = client.messages.create(
            from_=from_phone,
            body=message,
            to=to_phone
        )
        
        if message_obj.sid:
            # Log SMS details for both environments
            return True
        else:
            return False

    except TwilioException as e:
        return False
    except Exception as e:
        return False

def send_otp_sms(to_phone: str, otp_code: str, expires_minutes: int = 120):
    """
    Send OTP SMS with formatted message
    Sends actual SMS in both development and production
    """
    message = f"Your Manna Donate verification code is: {otp_code}. This code will expire in {expires_minutes} minutes. If you didn't request this code, please ignore this message."
    
    return send_sms_with_twilio(
        to_phone=to_phone,
        message=message,
        from_phone=config.TWILIO_PHONE_NUMBER
    )

def send_password_reset_sms(to_phone: str, reset_code: str, expires_minutes: int = 120):
    """
    Send password reset SMS
    Sends actual SMS in both development and production
    """
    message = f"Your Manna Donate password reset code is: {reset_code}. This code will expire in {expires_minutes} minutes. If you didn't request this code, please ignore this message."
    
    return send_sms_with_twilio(
        to_phone=to_phone,
        message=message,
        from_phone=config.TWILIO_PHONE_NUMBER
    )

def send_verification_sms(to_phone: str, verification_code: str):
    """
    Send verification SMS for profile verification
    """
    message = f"Your Manna Donate verification code is: {verification_code}. This code will expire in 10 minutes. If you didn't request this code, please ignore this message."
    
    return send_sms_with_twilio(
        to_phone=to_phone,
        message=message,
        from_phone=config.TWILIO_PHONE_NUMBER
    )

def test_twilio_connection():
    """
    Test Twilio connection and configuration
    """
    try:
        if not config.TWILIO_ACCOUNT_SID:
            return False
            
        if not config.TWILIO_AUTH_TOKEN:
            return False
            
        if not config.TWILIO_PHONE_NUMBER:
            return False
            
        # Test API credentials by creating a Twilio client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Try to get account info to test connection
        try:
            # This will test if the credentials are valid
            account = client.api.accounts(config.TWILIO_ACCOUNT_SID).fetch()
            return True
        except Exception as e:
            return False
            
    except Exception as e:
        return False 
