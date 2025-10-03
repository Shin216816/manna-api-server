from app.utils.token_manager import token_manager
import logging

def clean_expired_tokens():
    """Clean up expired refresh tokens and blacklisted tokens"""
    try:
        cleaned_count = token_manager.cleanup_expired_tokens()
        return cleaned_count
    except Exception as e:
        return 0

# Legacy function for backward compatibility
def clean_expired_blacklist():
    """Legacy function - use clean_expired_tokens instead"""
    return clean_expired_tokens()
