"""
Admin Registration Code Validator

Validates admin registration codes using the generated code system.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging


class AdminCodeValidator:
    """Validates admin registration codes against generated codes."""
    
    def __init__(self, code_file_path: str | None = None):
        """
        Initialize the validator.
        
        Args:
            code_file_path: Path to the admin registration code JSON file
        """
        if code_file_path:
            self.code_file_path = Path(code_file_path)
        else:
            # Default to the generated code file in the project root
            self.code_file_path = Path(__file__).parent.parent.parent / 'admin_registration_code.json'
        
        self._cached_code_data = None
    
    def load_code_data(self) -> Optional[Dict[str, Any]]:
        """
        Load the registration code data from the JSON file.
        
        Returns:
            Dict containing code data or None if file doesn't exist
        """
        if self._cached_code_data is not None:
            return self._cached_code_data
        
        if not self.code_file_path.exists():
            warning(f"Admin registration code file not found: {self.code_file_path}")
            return None
        
        try:
            with open(self.code_file_path, 'r') as f:
                self._cached_code_data = json.load(f)
            return self._cached_code_data
        except Exception as e:
            error(f"Error loading admin registration code file: {e}")
            return None
    
    def validate_code(self, provided_code: str) -> bool:
        """
        Validate a provided registration code.
        
        Args:
            provided_code: The code to validate
            
        Returns:
            True if code is valid, False otherwise
        """
        code_data = self.load_code_data()
        if not code_data:
            warning("No admin registration code data available")
            return False
        
        stored_code = code_data.get('registration_code')
        if not stored_code:
            warning("No registration code found in code data")
            return False
        
        # Direct comparison
        if provided_code == stored_code:
            info("Admin registration code validated successfully")
            return True
        
        # Check if code has expired (optional - codes don't expire by default)
        generated_at = code_data.get('generated_at')
        if generated_at:
            try:
                generated_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                # Optional: Add expiration logic here if needed
                # For now, codes don't expire
                pass
            except Exception as e:
                warning(f"Error parsing generation time: {e}")
        
        warning(f"Invalid admin registration code provided: {provided_code[:8]}...")
        return False
    
    def get_code_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current registration code.
        
        Returns:
            Dict with code information or None if not available
        """
        code_data = self.load_code_data()
        if not code_data:
            return None
        
        return {
            'generated_at': code_data.get('generated_at'),
            'config_hash': code_data.get('config_hash'),
            'code_prefix': code_data.get('registration_code', '')[:10] + '...' if code_data.get('registration_code') else None
        }
    
    def refresh_cache(self):
        """Refresh the cached code data."""
        self._cached_code_data = None

# Global validator instance
admin_code_validator = AdminCodeValidator()

def validate_admin_registration_code(code: str) -> bool:
    """
    Convenience function to validate admin registration codes.
    
    Args:
        code: The registration code to validate
        
    Returns:
        True if code is valid, False otherwise
    """
    return admin_code_validator.validate_code(code)

def get_admin_code_info() -> Optional[Dict[str, Any]]:
    """
    Get information about the current admin registration code.
    
    Returns:
        Dict with code information or None if not available
    """
    return admin_code_validator.get_code_info()
