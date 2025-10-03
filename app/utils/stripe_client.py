import stripe
from app.config import config

stripe.api_key = config.STRIPE_SECRET_KEY

# Re-export stripe module for proper typing
__all__ = ['stripe']

