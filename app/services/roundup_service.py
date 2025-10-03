"""
Unified Roundup Service for Manna Backend API.

This service is now a wrapper around RoundupEngine for API compatibility.
All functionality has been consolidated into RoundupEngine.
"""

from app.services.roundup_engine import RoundupEngine

class RoundupService:
    """Unified roundup service - wrapper around RoundupEngine for API compatibility"""
    
    @staticmethod
    def calculate_roundups(
        user_id: int, 
        start_date: str, 
        end_date: str, 
        db, 
        multiplier: float = 1.0, 
        days_back: int = 30
    ):
        """Calculate roundups - delegates to RoundupEngine"""
        return RoundupEngine.calculate_roundups(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            db=db,
            multiplier=multiplier,
            days_back=days_back
        )

# Create service instance for backward compatibility
roundup_service = RoundupService()