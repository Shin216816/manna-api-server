"""
Payment Service

Handles payment processing through Stripe for roundup collections.
Manages donor payments and church payouts with proper Stripe Connect integration.
"""

import logging
import stripe
from typing import Dict, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_roundup_new import DonorPayout, ChurchPayout
# PaymentMethod model removed - using Stripe API directly
from app.core.exceptions import PaymentError, ValidationError
from app.utils.error_handler import handle_service_errors
from app.config import config as settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    """Service for processing payments through Stripe"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    @handle_service_errors
    def process_donor_payment(self, user_id: int, amount: float, church_id: int, payout_id: int) -> Dict:
        """
        Process a donor payment through Stripe
        
        Args:
            user_id: User ID
            amount: Payment amount
            church_id: Target church ID
            payout_id: Donor payout ID
        
        Returns:
            Payment processing results
        """
        try:
            # Get user and church
            user = self.db.query(User).filter(User.id == user_id).first()
            church = self.db.query(Church).filter(Church.id == church_id).first()
            
            if not user:
                raise ValidationError("User not found")
            if not church:
                raise ValidationError("Church not found")
            
            # Validate amount
            if amount <= 0:
                raise ValidationError("Payment amount must be greater than 0")
            
            # Get or create Stripe customer
            customer_id = self._get_or_create_stripe_customer(user)
            
            # Get user's default payment method
            payment_method = self._get_default_payment_method(customer_id)
            
            if not payment_method:
                return {
                    'success': False,
                    'error': 'No payment method found. Please add a payment method.',
                    'requires_payment_method': True
                }
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                customer=customer_id,
                payment_method=payment_method,
                confirmation_method='automatic',
                confirm=True,
                metadata={
                    'user_id': str(user_id),
                    'church_id': str(church_id),
                    'payout_id': str(payout_id),
                    'type': 'roundup_collection'
                }
            )
            
            if payment_intent.status == 'succeeded':
                # Update donor payout with Stripe payment ID
                donor_payout = self.db.query(DonorPayout).filter(DonorPayout.id == payout_id).first()
                if donor_payout:
                    donor_payout.stripe_payment_intent_id = payment_intent.id
                    donor_payout.status = 'completed'
                    donor_payout.processed_at = datetime.now(timezone.utc)
                    self.db.commit()
                
                logger.info(f"Payment succeeded for user {user_id}: ${amount}")
                
                return {
                    'success': True,
                    'payment_intent_id': payment_intent.id,
                    'amount': amount,
                    'status': 'completed'
                }
            else:
                return {
                    'success': False,
                    'error': f'Payment failed with status: {payment_intent.status}',
                    'payment_intent_id': payment_intent.id,
                    'status': payment_intent.status
                }
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payment for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Payment processing error: {str(e)}',
                'stripe_error': True
            }
        except Exception as e:
            logger.error(f"Error processing payment for user {user_id}: {str(e)}")
            raise
    
    @handle_service_errors
    def process_church_payout(self, church_id: int, amount: float) -> Dict:
        """
        Process a payout to a church through Stripe Connect
        
        Args:
            church_id: Church ID
            amount: Payout amount
        
        Returns:
            Payout processing results
        """
        try:
            # Get church
            church = self.db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise ValidationError("Church not found")
            
            # Validate amount
            if amount <= 0:
                raise ValidationError("Payout amount must be greater than 0")
            
            # Check if church has Stripe Connect account
            if not church.stripe_account_id:
                return {
                    'success': False,
                    'error': 'Church has not completed Stripe Connect setup',
                    'requires_stripe_setup': True
                }
            
            # Check if church's Stripe account is ready for payouts
            if not church.charges_enabled or not church.payouts_enabled:
                return {
                    'success': False,
                    'error': 'Church Stripe account is not fully activated',
                    'requires_stripe_activation': True
                }
            
            # Create transfer to church's Stripe Connect account
            transfer = stripe.Transfer.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                destination=church.stripe_account_id,
                metadata={
                    'church_id': str(church_id),
                    'church_name': church.name,
                    'type': 'roundup_payout'
                }
            )
            
            # Update church payout record
            church_payout = self.db.query(ChurchPayout).filter(
                ChurchPayout.church_id == church_id,
                ChurchPayout.status == 'pending'
            ).first()
            
            if church_payout:
                church_payout.stripe_transfer_id = transfer.id
                church_payout.status = 'completed'
                church_payout.processed_at = datetime.now(timezone.utc)
                self.db.commit()
            
            logger.info(f"Payout succeeded for church {church_id}: ${amount}")
            
            return {
                'success': True,
                'transfer_id': transfer.id,
                'amount': amount,
                'status': 'completed'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payout for church {church_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Payout processing error: {str(e)}',
                'stripe_error': True
            }
        except Exception as e:
            logger.error(f"Error processing payout for church {church_id}: {str(e)}")
            raise
    
    @handle_service_errors
    def create_payment_method(self, user_id: int, payment_method_data: Dict) -> Dict:
        """
        Create a payment method for a user
        
        Args:
            user_id: User ID
            payment_method_data: Payment method data from frontend
        
        Returns:
            Payment method creation results
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationError("User not found")
            
            # Validate payment method data
            if 'card' not in payment_method_data:
                raise ValidationError("Card information is required")
            
            # Get or create Stripe customer
            customer_id = self._get_or_create_stripe_customer(user)
            
            # Create payment method
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card=payment_method_data['card'],
                billing_details=payment_method_data.get('billing_details', {
                    'name': f"{user.first_name} {user.last_name}",
                    'email': user.email
                })
            )
            
            # Attach to customer
            stripe.PaymentMethod.attach(
                payment_method.id,
                customer=customer_id
            )
            
            # Set as default if specified
            if payment_method_data.get('set_as_default', False):
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method.id
                    }
                )
                user.stripe_default_payment_method_id = payment_method.id
                self.db.commit()
            
            # Payment method is automatically stored in Stripe
            logger.info(f"Payment method created for user {user_id}: {payment_method.id}")
            
            return {
                'success': True,
                'payment_method_id': payment_method.id,
                'customer_id': customer_id,
                'is_default': payment_method_data.get('set_as_default', False)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment method for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Payment method creation error: {str(e)}',
                'stripe_error': True
            }
        except Exception as e:
            logger.error(f"Error creating payment method for user {user_id}: {str(e)}")
            raise
    
    @handle_service_errors
    def get_payment_methods(self, user_id: int) -> Dict:
        """
        Get payment methods for a user
        
        Args:
            user_id: User ID
        
        Returns:
            User's payment methods
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationError("User not found")
            
            # Get or create Stripe customer
            customer_id = self._get_or_create_stripe_customer(user)
            
            # Get payment methods from Stripe
            stripe_payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            # Format payment methods
            payment_methods = []
            for pm in stripe_payment_methods.data:
                payment_methods.append({
                    'id': pm.id,
                    'type': pm.type,
                    'card': {
                        'brand': pm.card.brand,
                        'last4': pm.card.last4,
                        'exp_month': pm.card.exp_month,
                        'exp_year': pm.card.exp_year
                    },
                    'is_default': pm.id == user.stripe_default_payment_method_id,
                    'created_at': datetime.fromtimestamp(pm.created).isoformat()
                })
            
            return {
                'success': True,
                'payment_methods': payment_methods,
                'customer_id': customer_id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting payment methods for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error retrieving payment methods: {str(e)}',
                'stripe_error': True
            }
        except Exception as e:
            logger.error(f"Error getting payment methods for user {user_id}: {str(e)}")
            raise
    
    def _get_or_create_stripe_customer(self, user: User) -> str:
        """Get or create Stripe customer for user"""
        if user.stripe_customer_id:
            return user.stripe_customer_id
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            metadata={
                'user_id': str(user.id),
                'user_type': user.role
            }
        )
        
        # Update user record
        user.stripe_customer_id = customer.id
        self.db.commit()
        
        return customer.id
    
    def _get_default_payment_method(self, customer_id: str) -> Optional[str]:
        """Get default payment method for customer"""
        customer = stripe.Customer.retrieve(customer_id)
        return customer.invoice_settings.default_payment_method
    
    @handle_service_errors
    def create_stripe_connect_account(self, church_id: int) -> Dict:
        """
        Create Stripe Connect account for church
        
        Args:
            church_id: Church ID
        
        Returns:
            Stripe Connect account creation results
        """
        try:
            # Get church
            church = self.db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise ValidationError("Church not found")
            
            if church.stripe_account_id:
                return {
                    'success': True,
                    'account_id': church.stripe_account_id,
                    'message': 'Stripe Connect account already exists'
                }
            
            # Create Stripe Connect account
            account = stripe.Account.create(
                type='express',
                country='US',
                email=church.email,
                metadata={
                    'church_id': str(church_id),
                    'church_name': church.name
                }
            )
            
            # Update church record
            church.stripe_account_id = account.id
            self.db.commit()
            
            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=f"{settings.FRONTEND_URL}/church/onboarding/stripe-return",
                return_url=f"{settings.FRONTEND_URL}/church/onboarding/stripe-return",
                type='account_onboarding'
            )
            
            logger.info(f"Stripe Connect account created for church {church_id}: {account.id}")
            
            return {
                'success': True,
                'account_id': account.id,
                'onboarding_url': account_link.url,
                'expires_at': account_link.expires_at
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating Connect account for church {church_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Stripe Connect account creation error: {str(e)}',
                'stripe_error': True
            }
        except Exception as e:
            logger.error(f"Error creating Stripe Connect account for church {church_id}: {str(e)}")
            raise
    
    @handle_service_errors
    def get_stripe_connect_status(self, church_id: int) -> Dict:
        """
        Get Stripe Connect account status for church
        
        Args:
            church_id: Church ID
        
        Returns:
            Stripe Connect account status
        """
        try:
            # Get church
            church = self.db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise ValidationError("Church not found")
            
            if not church.stripe_account_id:
                return {
                    'success': True,
                    'has_account': False,
                    'status': 'not_created'
                }
            
            # Get account details from Stripe
            account = stripe.Account.retrieve(church.stripe_account_id)
            
            # Update church status
            church.charges_enabled = account.charges_enabled
            church.payouts_enabled = account.payouts_enabled
            self.db.commit()
            
            return {
                'success': True,
                'has_account': True,
                'account_id': account.id,
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'details_submitted': account.details_submitted,
                'status': 'active' if account.charges_enabled and account.payouts_enabled else 'pending'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting Connect status for church {church_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error retrieving Stripe Connect status: {str(e)}',
                'stripe_error': True
            }
        except Exception as e:
            logger.error(f"Error getting Stripe Connect status for church {church_id}: {str(e)}")
            raise
