"""
Business validation utilities for church onboarding and KYC processes.
Handles EIN validation, phone number normalization, and other business identifiers.
"""

import re
from typing import Optional


def normalize_ein(ein: Optional[str]) -> Optional[str]:
    """
    Normalize EIN by removing all non-digit characters.
    
    Args:
        ein: The EIN string to normalize (e.g., "12-3456789" or "123456789")
        
    Returns:
        The normalized EIN with only digits, or None if input is None/empty
        
    Example:
        normalize_ein("12-3456789") -> "123456789"
        normalize_ein("12 3456789") -> "123456789"
        normalize_ein("123456789") -> "123456789"
    """
    if not ein:
        return None
    return ''.join(filter(str.isdigit, ein))


def normalize_ssn(ssn: Optional[str]) -> Optional[str]:
    """
    Normalize SSN by removing all non-digit characters.
    
    Args:
        ssn: The SSN string to normalize
        
    Returns:
        The normalized SSN with only digits, or None if input is None/empty
        
    Example:
        normalize_ssn("123-45-6789") -> "123456789"
        normalize_ssn("123 45 6789") -> "123456789"
    """
    if not ssn:
        return None
    return ''.join(filter(str.isdigit, ssn))
