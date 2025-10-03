"""
Admin Invitation Validator

Validates admin invitation codes from the invitation system.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging


class InvitationValidator:
    """Validates admin invitation codes."""
    
    def __init__(self, invitations_file_path: str | None = None):
        """
        Initialize the validator.
        
        Args:
            invitations_file_path: Path to the admin invitations JSON file
        """
        if invitations_file_path:
            self.invitations_file = Path(invitations_file_path)
        else:
            # Default to the generated invitations file in the project root
            self.invitations_file = Path(__file__).parent.parent.parent / 'admin_invitations.json'
        
        self._cached_invitations: Optional[Dict[str, Any]] = None
    
    def load_invitations(self) -> Optional[Dict[str, Any]]:
        """
        Load the invitations data from the JSON file.
        
        Returns:
            Dict containing invitations data or None if file doesn't exist
        """
        if self._cached_invitations is not None:
            return self._cached_invitations
        
        if not self.invitations_file.exists():
            return None
        
        try:
            with open(self.invitations_file, 'r') as f:
                self._cached_invitations = json.load(f)
            return self._cached_invitations
        except Exception as e:
            return None
    
    def find_invitation_by_code(self, invitation_code: str) -> Optional[Dict[str, Any]]:
        """
        Find invitation by code.
        
        Args:
            invitation_code: The invitation code to find
            
        Returns:
            Invitation data or None if not found
        """
        invitations_data = self.load_invitations()
        if not invitations_data:
            return None
        
        invitations = invitations_data.get('invitations', [])
        for invitation in invitations:
            if invitation.get('invitation_code') == invitation_code:
                return invitation
        
        return None
    
    def validate_invitation(self, invitation_code: str) -> Dict[str, Any]:
        """
        Validate an invitation code.
        
        Args:
            invitation_code: The invitation code to validate
            
        Returns:
            Dict with validation result
        """
        invitation = self.find_invitation_by_code(invitation_code)
        
        if not invitation:
            return {
                "valid": False,
                "error": "Invalid invitation code"
            }
        
        # Check if already used
        if invitation.get('is_used', False):
            return {
                "valid": False,
                "error": "Invitation code has already been used"
            }
        
        # Check if expired
        expires_at_str = invitation.get('expires_at')
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                
                if now > expires_at:
                    return {
                        "valid": False,
                        "error": "Invitation code has expired"
                    }
            except Exception as e:
                pass
        
        return {
            "valid": True,
            "invitation": invitation
        }
    
    def mark_invitation_used(self, invitation_code: str, admin_email: str) -> bool:
        """
        Mark an invitation as used.
        
        Args:
            invitation_code: The invitation code to mark as used
            admin_email: The email of the admin who used the invitation
            
        Returns:
            True if successful, False otherwise
        """
        invitations_data = self.load_invitations()
        if not invitations_data:
            return False
        
        invitations = invitations_data.get('invitations', [])
        for invitation in invitations:
            if invitation.get('invitation_code') == invitation_code:
                invitation['is_used'] = True
                invitation['used_at'] = datetime.now(timezone.utc).isoformat()
                invitation['used_by'] = admin_email
                
                # Save updated invitations
                try:
                    with open(self.invitations_file, 'w') as f:
                        json.dump(invitations_data, f, indent=2)
                    
                    # Refresh cache
                    self._cached_invitations = invitations_data
                    
                    return True
                except Exception as e:
                    return False
        
        return False
    
    def get_invitation_info(self, invitation_code: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an invitation.
        
        Args:
            invitation_code: The invitation code
            
        Returns:
            Invitation info or None if not found
        """
        invitation = self.find_invitation_by_code(invitation_code)
        if not invitation:
            return None
        
        return {
            'email': invitation.get('email'),
            'name': invitation.get('name'),
            'created_at': invitation.get('created_at'),
            'expires_at': invitation.get('expires_at'),
            'is_used': invitation.get('is_used', False),
            'used_at': invitation.get('used_at'),
            'created_by': invitation.get('created_by')
        }
    
    def refresh_cache(self):
        """Refresh the cached invitations data."""
        self._cached_invitations = None

# Global validator instance
invitation_validator = InvitationValidator()

def validate_admin_invitation(code: str) -> Dict[str, Any]:
    """
    Convenience function to validate admin invitation codes.
    
    Args:
        code: The invitation code to validate
        
    Returns:
        Dict with validation result
    """
    return invitation_validator.validate_invitation(code)

def mark_admin_invitation_used(code: str, admin_email: str) -> bool:
    """
    Convenience function to mark admin invitation as used.
    
    Args:
        code: The invitation code to mark as used
        admin_email: The email of the admin who used the invitation
        
    Returns:
        True if successful, False otherwise
    """
    return invitation_validator.mark_invitation_used(code, admin_email)

def get_admin_invitation_info(code: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get admin invitation info.
    
    Args:
        code: The invitation code
        
    Returns:
        Invitation info or None if not found
    """
    return invitation_validator.get_invitation_info(code)
