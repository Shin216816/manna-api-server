"""
Mobile Legal Controller

Handles legal documents for mobile app:
- Terms of service
- Privacy policy
"""

from fastapi import HTTPException
import logging
from app.core.responses import ResponseFactory


def get_terms_of_service():
    """Get terms of service for mobile app"""
    try:
        terms_data = {
            "title": "Terms of Service",
            "version": "1.0",
            "last_updated": "2024-01-15",
            "content": """
            # Terms of Service
            
            ## 1. Acceptance of Terms
            By accessing and using the Manna Donate mobile application, you accept and agree to be bound by the terms and provision of this agreement.
            
            ## 2. Description of Service
            Manna Donate provides a platform for charitable giving through roundup donations and direct contributions to churches and religious organizations.
            
            ## 3. User Accounts
            You are responsible for maintaining the confidentiality of your account information and for all activities that occur under your account.
            
            ## 4. Privacy Policy
            Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the Service.
            
            ## 5. Prohibited Uses
            You may not use the Service for any unlawful purpose or to solicit others to perform or participate in any unlawful acts.
            
            ## 6. Termination
            We may terminate or suspend your account and bar access to the Service immediately, without prior notice or liability.
            
            ## 7. Changes to Terms
            We reserve the right to modify or replace these Terms at any time.
            
            ## 8. Contact Information
            If you have any questions about these Terms, please contact us at support@mannadonate.com.
            """
        }
        
        return ResponseFactory.success(
            message="Terms of service retrieved successfully",
            data=terms_data
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve terms of service")


def get_privacy_policy():
    """Get privacy policy for mobile app"""
    try:
        privacy_data = {
            "title": "Privacy Policy",
            "version": "1.0",
            "last_updated": "2024-01-15",
            "content": """
            # Privacy Policy
            
            ## 1. Information We Collect
            We collect information you provide directly to us, such as when you create an account, make a donation, or contact us for support.
            
            ## 2. How We Use Your Information
            We use the information we collect to provide, maintain, and improve our services, process transactions, and communicate with you.
            
            ## 3. Information Sharing
            We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy.
            
            ## 4. Data Security
            We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.
            
            ## 5. Data Retention
            We retain your personal information for as long as necessary to provide our services and comply with legal obligations.
            
            ## 6. Your Rights
            You have the right to access, update, or delete your personal information. You may also opt out of certain communications.
            
            ## 7. Cookies and Tracking
            We use cookies and similar technologies to enhance your experience and analyze usage patterns.
            
            ## 8. Third-Party Services
            Our service may contain links to third-party websites or services. We are not responsible for their privacy practices.
            
            ## 9. Children's Privacy
            Our service is not intended for children under 13. We do not knowingly collect personal information from children under 13.
            
            ## 10. Changes to This Policy
            We may update this privacy policy from time to time. We will notify you of any changes by posting the new policy on this page.
            
            ## 11. Contact Us
            If you have any questions about this Privacy Policy, please contact us at privacy@mannadonate.com.
            """
        }
        
        return ResponseFactory.success(
            message="Privacy policy retrieved successfully",
            data=privacy_data
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to retrieve privacy policy")
