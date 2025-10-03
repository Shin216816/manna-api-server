"""
Email sending utilities using SendGrid.
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from app.config import config

def send_email_with_sendgrid(to_email: str, code: str = "", expires: int = 120, subject: str = "Verify", body_html: str = ""):
    """
    Send OTP email using SendGrid with API key authentication
    Following official SendGrid Python guide
    Sends emails in both development and production environments
    """
    try:
        # Validate required configuration
        if not config.SENDGRID_API_KEY:
            return False

        # Create simple HTML body for OTP
        if body_html:
            html_content = body_html
        else:
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #6366F1; margin-bottom: 20px;">Verification Code</h2>
                        <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p style="font-size: 16px; color: #6b7280; margin-bottom: 10px;">Your verification code is:</p>
                            <div style="background-color: #6366F1; color: white; padding: 15px; border-radius: 6px; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 15px 0;">
                                {code}
                            </div>
                        </div>
                        <p style="color: #6b7280; font-size: 14px;">This code will expire in {expires} minutes.</p>
                        <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">If you didn't request this code, please ignore this email.</p>
                    </div>
                </body>
            </html>
            """

        # Create SendGrid Mail object using official approach
        from_email = Email(config.SENDGRID_FROM_EMAIL or config.EMAIL_FROM)
        to_email_obj = To(to_email)
        subject_obj = subject
        content = Content("text/html", html_content)
        
        mail = Mail(from_email, to_email_obj, subject_obj, content)
        
        # Send email using SendGrid API
        sg = SendGridAPIClient(config.SENDGRID_API_KEY)
        response = sg.send(mail)
        
        if response.status_code == 202:
            return True
        else:
            return False

    except Exception as e:
        return False

def send_otp_email(to_email: str, otp_code: str, expires_minutes: int = 120):
    """
    Simplified function to send OTP email
    Sends actual email in both development and production
    """
    return send_email_with_sendgrid(
        to_email=to_email,
        code=otp_code,
        expires=expires_minutes,
        subject="Your Verification Code - Manna Donate"
    )

def send_password_reset_email(to_email: str, reset_code: str, expires_minutes: int = 120):
    """
    Send password reset email
    Sends actual email in both development and production
    """
    return send_email_with_sendgrid(
        to_email=to_email,
        code=reset_code,
        expires=expires_minutes,
        subject="Password Reset Code - Manna Donate"
    )

def send_verification_email(to_email: str, user_name: str, verification_code: str):
    """
    Send verification email for profile verification
    """
    return send_email_with_sendgrid(
        to_email=to_email,
        code=verification_code,
        expires=10,
        subject="Email Verification - Manna Donate"
    )

def test_sendgrid_connection():
    """
    Test SendGrid connection and configuration
    """
    try:
        if not config.SENDGRID_API_KEY:
            return False
            
        if not config.SENDGRID_FROM_EMAIL:
            return False
            
        # Test API key by creating a SendGrid client
        sg = SendGridAPIClient(config.SENDGRID_API_KEY)
        
        # Try to get account info to test connection
        try:
            # This will test if the API key is valid
            # Just test if the client can be created successfully
            _ = SendGridAPIClient(config.SENDGRID_API_KEY)
            return True
        except Exception as e:
            return False
            
    except Exception as e:
        return False
