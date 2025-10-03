"""
Email Service

Handles email sending for verification, notifications, and other communications.
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.model.m_user import User
from app.model.m_email_verification import EmailVerification
from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.core.exceptions import EmailError, ValidationError
from app.utils.error_handler import handle_service_errors
from app.config import config as settings
import secrets
import hashlib

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    @handle_service_errors
    def send_verification_email(self, user_id: int) -> Dict:
        """
        Send email verification to a user
        
        Args:
            user_id: User ID
        
        Returns:
            Email sending results
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationError("User not found")
            
            if user.is_email_verified:
                return {
                    'success': False,
                    'message': 'Email already verified'
                }
            
            # Create verification token
            verification_token = self._create_verification_token(user_id)
            
            # Send verification email
            subject = "Verify Your Manna Account"
            html_content = self._get_verification_email_html(user, verification_token)
            text_content = self._get_verification_email_text(user, verification_token)
            
            success = self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Verification email sent successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send verification email'
                }
                
        except Exception as e:
            logger.error(f"Error sending verification email to user {user_id}: {str(e)}")
            raise
    
    @handle_service_errors
    def verify_email(self, token: str) -> Dict:
        """
        Verify user's email with token
        
        Args:
            token: Verification token
        
        Returns:
            Verification results
        """
        try:
            # Find verification record
            verification = self.db.query(EmailVerification).filter(
                EmailVerification.token == token,
                EmailVerification.status == 'pending'
            ).first()
            
            if not verification:
                return {
                    'success': False,
                    'message': 'Invalid or expired verification token'
                }
            
            # Check if token is expired
            if verification.expires_at < datetime.now(timezone.utc):
                verification.status = 'expired'
                self.db.commit()
                return {
                    'success': False,
                    'message': 'Verification token has expired'
                }
            
            # Get user
            user = self.db.query(User).filter(User.id == verification.user_id).first()
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Verify user's email
            user.is_email_verified = True
            verification.status = 'verified'
            verification.verified_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Email verified for user {user.id}")
            
            return {
                'success': True,
                'message': 'Email verified successfully'
            }
            
        except Exception as e:
            logger.error(f"Error verifying email with token {token}: {str(e)}")
            raise
    
    @handle_service_errors
    def send_password_reset_email(self, email: str) -> Dict:
        """
        Send password reset email
        
        Args:
            email: User's email address
        
        Returns:
            Email sending results
        """
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                # Don't reveal if email exists or not
                return {
                    'success': True,
                    'message': 'If the email exists, a password reset link has been sent'
                }
            
            # Create password reset token
            reset_token = self._create_password_reset_token(user.id)
            
            # Send password reset email
            subject = "Reset Your Manna Password"
            html_content = self._get_password_reset_email_html(user, reset_token)
            text_content = self._get_password_reset_email_text(user, reset_token)
            
            success = self._send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Password reset email sent successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send password reset email'
                }
                
        except Exception as e:
            logger.error(f"Error sending password reset email to {email}: {str(e)}")
            raise
    
    @handle_service_errors
    def send_kyc_approval_email(self, church_id: int) -> Dict:
        """
        Send KYC approval email to church admin
        
        Args:
            church_id: Church ID
        
        Returns:
            Email sending results
        """
        try:
            from app.model.m_church import Church
            from app.model.m_church_admin import ChurchAdmin
            
            church = self.db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise ValidationError("Church not found")
            
            church_admin = self.db.query(ChurchAdmin).filter(
                ChurchAdmin.church_id == church_id
            ).first()
            
            if not church_admin:
                raise ValidationError("Church admin not found")
            
            # Send approval email
            subject = "Your Church KYC Has Been Approved - Welcome to Manna!"
            html_content = self._get_kyc_approval_email_html(church, church_admin)
            text_content = self._get_kyc_approval_email_text(church, church_admin)
            
            success = self._send_email(
                to_email=church_admin.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'KYC approval email sent successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send KYC approval email'
                }
                
        except Exception as e:
            logger.error(f"Error sending KYC approval email for church {church_id}: {str(e)}")
            raise
    
    def _create_verification_token(self, user_id: int) -> str:
        """Create email verification token"""
        # Generate random token
        token = secrets.token_urlsafe(32)
        
        # Create verification record
        verification = EmailVerification(
            user_id=user_id,
            token=token,
            type='email_verification',
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            status='pending',
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(verification)
        self.db.commit()
        
        return token
    
    def _create_password_reset_token(self, user_id: int) -> str:
        """Create password reset token"""
        # Generate random token
        token = secrets.token_urlsafe(32)
        
        # Create verification record
        verification = EmailVerification(
            user_id=user_id,
            token=token,
            type='password_reset',
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            status='pending',
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(verification)
        self.db.commit()
        
        return token
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def _get_verification_email_html(self, user: User, token: str) -> str:
        """Get HTML content for verification email"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Manna Account</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2563eb;">Welcome to Manna!</h1>
            <p>Hi {user.first_name},</p>
            <p>Thank you for signing up for Manna! To complete your account setup, please verify your email address by clicking the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Verify Email Address</a>
            </div>
            <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with Manna, you can safely ignore this email.</p>
            <p>Best regards,<br>The Manna Team</p>
        </body>
        </html>
        """
    
    def _get_verification_email_text(self, user: User, token: str) -> str:
        """Get text content for verification email"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        return f"""
        Welcome to Manna!
        
        Hi {user.first_name},
        
        Thank you for signing up for Manna! To complete your account setup, please verify your email address by visiting this link:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account with Manna, you can safely ignore this email.
        
        Best regards,
        The Manna Team
        """
    
    def _get_password_reset_email_html(self, user: User, token: str) -> str:
        """Get HTML content for password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Manna Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2563eb;">Reset Your Password</h1>
            <p>Hi {user.first_name},</p>
            <p>We received a request to reset your Manna password. Click the button below to create a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Reset Password</a>
            </div>
            <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, you can safely ignore this email.</p>
            <p>Best regards,<br>The Manna Team</p>
        </body>
        </html>
        """
    
    def _get_password_reset_email_text(self, user: User, token: str) -> str:
        """Get text content for password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        return f"""
        Reset Your Password
        
        Hi {user.first_name},
        
        We received a request to reset your Manna password. Visit this link to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        Best regards,
        The Manna Team
        """
    
    def _get_kyc_approval_email_html(self, church: Church, church_admin: ChurchAdmin) -> str:
        """Get HTML content for KYC approval email"""
        dashboard_url = f"{settings.FRONTEND_URL}/church-admin/dashboard"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your Church KYC Has Been Approved</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #16a34a;">Congratulations! Your Church KYC Has Been Approved</h1>
            <p>Hi {church_admin.admin_name},</p>
            <p>Great news! Your church "{church.name}" has been approved for Manna. You can now start receiving micro-donations from your congregation.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{dashboard_url}" style="background-color: #16a34a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Access Your Dashboard</a>
            </div>
            <p>Next steps:</p>
            <ul>
                <li>Share your church's unique signup link with your congregation</li>
                <li>Set up your church profile and preferences</li>
                <li>Start receiving roundup donations from your members</li>
            </ul>
            <p>If you have any questions, please don't hesitate to contact our support team.</p>
            <p>Welcome to Manna!<br>The Manna Team</p>
        </body>
        </html>
        """
    
    def _get_kyc_approval_email_text(self, church: Church, church_admin: ChurchAdmin) -> str:
        """Get text content for KYC approval email"""
        dashboard_url = f"{settings.FRONTEND_URL}/church-admin/dashboard"
        
        return f"""
        Congratulations! Your Church KYC Has Been Approved
        
        Hi {church_admin.admin_name},
        
        Great news! Your church "{church.name}" has been approved for Manna. You can now start receiving micro-donations from your congregation.
        
        Access your dashboard: {dashboard_url}
        
        Next steps:
        - Share your church's unique signup link with your congregation
        - Set up your church profile and preferences
        - Start receiving roundup donations from your members
        
        If you have any questions, please don't hesitate to contact our support team.
        
        Welcome to Manna!
        The Manna Team
        """
