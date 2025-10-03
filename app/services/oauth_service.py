"""
OAuth Service

Handles OAuth authentication for Google and Apple providers.
Provides token verification and user information extraction.
"""

import logging
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import jwt
from urllib.parse import urlencode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ValidationError
from app.utils.error_handler import handle_service_errors
from app.config import config as settings

logger = logging.getLogger(__name__)

class OAuthService:
    """Service for OAuth authentication"""
    
    def __init__(self):
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.apple_client_id = settings.APPLE_CLIENT_ID
        self.apple_team_id = settings.APPLE_TEAM_ID
        self.apple_key_id = settings.APPLE_KEY_ID
        self.apple_private_key = settings.APPLE_PRIVATE_KEY
    
    @handle_service_errors
    async def authenticate_google_user(self, id_token: str) -> Dict[str, Any]:
        """
        Authenticate user with Google ID token
        
        Args:
            id_token: Google ID token from client
        
        Returns:
            User information from Google
        """
        try:
            # Verify the ID token
            user_info = await self._verify_google_id_token(id_token)
            
            if not user_info:
                raise AuthenticationError("Invalid Google ID token")
            
            return {
                'google_id': user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'email_verified': user_info.get('email_verified', False),
                'provider': 'google'
            }
            
        except Exception as e:
            logger.error(f"Error authenticating Google user: {str(e)}")
            raise AuthenticationError(f"Google authentication failed: {str(e)}")
    
    @handle_service_errors
    async def authenticate_apple_user(self, id_token: str) -> Dict[str, Any]:
        """
        Authenticate user with Apple ID token
        
        Args:
            id_token: Apple ID token from client
        
        Returns:
            User information from Apple
        """
        try:
            # Verify the ID token
            user_info = await self._verify_apple_id_token(id_token)
            
            if not user_info:
                raise AuthenticationError("Invalid Apple ID token")
            
            return {
                'apple_id': user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'email_verified': user_info.get('email_verified', False),
                'provider': 'apple'
            }
            
        except Exception as e:
            logger.error(f"Error authenticating Apple user: {str(e)}")
            raise AuthenticationError(f"Apple authentication failed: {str(e)}")
    
    async def _verify_google_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Google ID token and extract user information"""
        try:
            # Get Google's public keys
            async with httpx.AsyncClient() as client:
                response = await client.get('https://www.googleapis.com/oauth2/v3/certs')
                response.raise_for_status()
                keys = response.json()
            
            # Decode the token header to get the key ID
            unverified_header = jwt.get_unverified_header(id_token)
            key_id = unverified_header.get('kid')
            
            if not key_id:
                raise AuthenticationError("No key ID found in token header")
            
            # Find the matching public key
            public_key = self._get_google_public_key(keys, key_id)
            if not public_key:
                raise AuthenticationError("No matching public key found")
            
            # Verify and decode the token
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=self.google_client_id,
                issuer='https://accounts.google.com'
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Google ID token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid Google ID token: {str(e)}")
        except Exception as e:
            logger.error(f"Error verifying Google ID token: {str(e)}")
            raise AuthenticationError(f"Token verification failed: {str(e)}")
    
    async def _verify_apple_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Apple ID token and extract user information"""
        try:
            # Get Apple's public keys
            async with httpx.AsyncClient() as client:
                response = await client.get('https://appleid.apple.com/auth/keys')
                response.raise_for_status()
                keys = response.json()
            
            # Decode the token header to get the key ID
            unverified_header = jwt.get_unverified_header(id_token)
            key_id = unverified_header.get('kid')
            
            if not key_id:
                raise AuthenticationError("No key ID found in token header")
            
            # Find the matching public key
            public_key = self._get_apple_public_key(keys, key_id)
            if not public_key:
                raise AuthenticationError("No matching public key found")
            
            # Verify and decode the token
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=self.apple_client_id,
                issuer='https://appleid.apple.com'
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Apple ID token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid Apple ID token: {str(e)}")
        except Exception as e:
            logger.error(f"Error verifying Apple ID token: {str(e)}")
            raise AuthenticationError(f"Token verification failed: {str(e)}")
    
    def _get_google_public_key(self, keys: Dict, key_id: str) -> Optional[str]:
        """Get Google public key by key ID"""
        for key in keys.get('keys', []):
            if key.get('kid') == key_id:
                return self._construct_public_key(key)
        return None
    
    def _get_apple_public_key(self, keys: Dict, key_id: str) -> Optional[str]:
        """Get Apple public key by key ID"""
        for key in keys.get('keys', []):
            if key.get('kid') == key_id:
                return self._construct_public_key(key)
        return None
    
    def _construct_public_key(self, key_data: Dict) -> str:
        """Construct public key from JWK data"""
        try:
            # Convert JWK to PEM format
            n = int.from_bytes(self._base64url_decode(key_data['n']), 'big')
            e = int.from_bytes(self._base64url_decode(key_data['e']), 'big')
            
            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
            
            # Serialize to PEM format
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error constructing public key: {str(e)}")
            return None
    
    def _base64url_decode(self, data: str) -> bytes:
        """Decode base64url encoded data"""
        # Add padding if needed
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        
        # Replace URL-safe characters
        data = data.replace('-', '+').replace('_', '/')
        
        import base64
        return base64.b64decode(data)
    
    @handle_service_errors
    async def refresh_google_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Google access token using refresh token
        
        Args:
            refresh_token: Google refresh token
        
        Returns:
            New access token information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post('https://oauth2.googleapis.com/token', data={
                    'client_id': self.google_client_id,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token'
                })
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error refreshing Google token: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    @handle_service_errors
    async def revoke_google_token(self, token: str) -> bool:
        """
        Revoke Google access token
        
        Args:
            token: Google access token to revoke
        
        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post('https://oauth2.googleapis.com/revoke', data={
                    'token': token
                })
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Error revoking Google token: {str(e)}")
            return False
    
    def validate_oauth_provider(self, provider: str) -> bool:
        """Validate OAuth provider"""
        valid_providers = ['google', 'apple']
        return provider.lower() in valid_providers
    
    def get_oauth_config(self, provider: str) -> Dict[str, Any]:
        """Get OAuth configuration for provider"""
        if provider.lower() == 'google':
            return {
                'client_id': self.google_client_id,
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': 'openid email profile'
            }
        elif provider.lower() == 'apple':
            return {
                'client_id': self.apple_client_id,
                'auth_url': 'https://appleid.apple.com/auth/authorize',
                'token_url': 'https://appleid.apple.com/auth/token',
                'scope': 'name email'
            }
        else:
            raise ValidationError(f"Unsupported OAuth provider: {provider}")
    
    @handle_service_errors
    async def exchange_google_code_for_user_info(self, code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """
        Exchange Google authorization code for user information
        
        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in the initial request
        
        Returns:
            User information from Google
        """
        try:
            from app.config import config
            
            # Default redirect URI if not provided - must match the one used in OAuth URL
            if not redirect_uri:
                # Always use the configured redirect URI if available
                if config.GOOGLE_REDIRECT_URI:
                    redirect_uri = config.GOOGLE_REDIRECT_URI
                else:
                    # Fallback based on environment if not configured
                    if config.ENVIRONMENT == "production":
                        redirect_uri = "https://manna-api-server.onrender.com/api/v1/donor/google-oauth/callback"
                    else:
                        redirect_uri = "http://localhost:8000/api/v1/donor/google-oauth/callback"
            
            # Validate required configuration
            if not config.GOOGLE_CLIENT_SECRET:
                raise AuthenticationError("Google Client Secret is not configured")
            
            # Exchange code for access token
            token_data = {
                'client_id': self.google_client_id,
                'client_secret': config.GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                # Get access token
                token_response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data=token_data
                )
                token_response.raise_for_status()
                token_result = token_response.json()
                
                access_token = token_result.get('access_token')
                if not access_token:
                    raise AuthenticationError("Failed to get access token from Google")
                
                # Get user info using access token
                user_response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                user_response.raise_for_status()
                user_info = user_response.json()
                
                return {
                    'google_id': user_info.get('id'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'given_name': user_info.get('given_name'),
                    'family_name': user_info.get('family_name'),
                    'picture': user_info.get('picture'),
                    'email_verified': user_info.get('verified_email', False),
                    'provider': 'google'
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error exchanging Google code: {e.response.status_code} - {e.response.text}")
            raise AuthenticationError(f"Google API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error exchanging Google code for user info: {str(e)}")
            raise AuthenticationError(f"Failed to exchange code for user info: {str(e)}")
    
    @handle_service_errors
    async def get_google_oauth_url(self, state: str, redirect_uri: str = None) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            state: State parameter for security
            redirect_uri: Optional redirect URI override
        
        Returns:
            Google OAuth authorization URL
        """
        try:
            from app.config import config
            
            # Default redirect URI if not provided
            if not redirect_uri:
                # Always use the configured redirect URI if available
                if config.GOOGLE_REDIRECT_URI:
                    redirect_uri = config.GOOGLE_REDIRECT_URI
                else:
                    # Fallback based on environment if not configured
                    if config.ENVIRONMENT == "production":
                        redirect_uri = "https://manna-api-server.onrender.com/api/v1/donor/google-oauth/callback"
                    else:
                        redirect_uri = "http://localhost:8000/api/v1/donor/google-oauth/callback"
            
            # Validate redirect URI format
            if not redirect_uri.startswith(('http://', 'https://')):
                raise ValidationError(f"Invalid redirect URI format: {redirect_uri}")
            
            # Validate client ID
            if not self.google_client_id:
                raise ValidationError("Google Client ID is not configured")
            
            # For production, ensure HTTPS
            if config.ENVIRONMENT == "production" and not redirect_uri.startswith('https://'):
                raise ValidationError("Production environment requires HTTPS redirect URI")
            
            # Build OAuth URL parameters
            params = {
                'client_id': self.google_client_id,
                'response_type': 'code',
                'scope': 'openid email profile',
                'redirect_uri': redirect_uri,
                'state': state,
                'access_type': 'offline',
                'prompt': 'consent'
            }
            
            # Construct the URL with proper encoding
            base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
            query_string = urlencode(params)
            oauth_url = f"{base_url}?{query_string}"
            
            return oauth_url
            
        except Exception as e:
            logger.error(f"Error generating Google OAuth URL: {str(e)}")
            raise ValidationError(f"Failed to generate OAuth URL: {str(e)}")
    
    @handle_service_errors  
    async def get_apple_oauth_url(self, state: str, redirect_uri: str = None) -> str:
        """
        Generate Apple OAuth authorization URL
        
        Args:
            state: State parameter for security
            redirect_uri: Optional redirect URI override
        
        Returns:
            Apple OAuth authorization URL
        """
        try:
            # Default redirect URI if not provided
            if not redirect_uri:
                redirect_uri = getattr(settings, 'APPLE_REDIRECT_URI', 'http://localhost:3000/auth/callback')
            
            # Build OAuth URL parameters
            params = {
                'client_id': self.apple_client_id,
                'response_type': 'code',
                'scope': 'name email',
                'redirect_uri': redirect_uri,
                'state': state,
                'response_mode': 'form_post'
            }
            
            # Construct the URL with proper encoding
            base_url = 'https://appleid.apple.com/auth/authorize'
            query_string = urlencode(params)
            oauth_url = f"{base_url}?{query_string}"
            
            return oauth_url
            
        except Exception as e:
            logger.error(f"Error generating Apple OAuth URL: {str(e)}")
            raise ValidationError(f"Failed to generate OAuth URL: {str(e)}")

    # Additional functions from other OAuth services for consolidation
    # These maintain API compatibility while consolidating services
    
    def exchange_authorization_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token and ID token (from google_oauth_service.py)
        Maintains API compatibility
        """
        try:
            import requests
            
            # Exchange authorization code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "code": authorization_code,
                "client_id": self.google_client_id,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
            
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_response = response.json()
            
            return {
                "access_token": token_response.get("access_token"),
                "id_token": token_response.get("id_token"),
                "expires_in": token_response.get("expires_in"),
                "token_type": token_response.get("token_type")
            }
            
        except Exception as e:
            logger.error(f"Error exchanging authorization code: {str(e)}")
            raise AuthenticationError(f"Failed to exchange authorization code: {str(e)}")
    
    def verify_google_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """
        Verify Google ID token (from google_oauth_service.py)
        Maintains API compatibility
        """
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token
            
            # Verify the ID token
            idinfo = google_id_token.verify_oauth2_token(
                id_token_str, 
                google_requests.Request(), 
                self.google_client_id
            )
            
            return {
                "sub": idinfo.get("sub"),
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "given_name": idinfo.get("given_name"),
                "family_name": idinfo.get("family_name"),
                "picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified", False)
            }
            
        except Exception as e:
            logger.error(f"Error verifying Google ID token: {str(e)}")
            raise AuthenticationError(f"Failed to verify Google ID token: {str(e)}")
    
    def create_or_get_user_from_google(self, google_data: Dict[str, Any], db: Session, user_type: str = "donor") -> Dict[str, Any]:
        """
        Create or get user from Google data (from google_oauth_service.py)
        Maintains API compatibility
        """
        try:
            from app.model.m_user import User
            from app.model.m_church_admin import ChurchAdmin
            from app.utils.jwt_handler import create_access_token
            
            email = google_data.get("email")
            if not email:
                raise ValidationError("Email is required for Google OAuth")
            
            # Check if user already exists
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Update user with Google data
                user.google_id = google_data.get("sub")
                user.first_name = google_data.get("given_name", user.first_name)
                user.last_name = google_data.get("family_name", user.last_name)
                user.profile_picture_url = google_data.get("picture", user.profile_picture_url)
                user.email_verified = google_data.get("email_verified", user.email_verified)
                user.updated_at = datetime.now(timezone.utc)
                
                db.commit()
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_data.get("sub"),
                    first_name=google_data.get("given_name", ""),
                    last_name=google_data.get("family_name", ""),
                    profile_picture_url=google_data.get("picture"),
                    email_verified=google_data.get("email_verified", False),
                    user_type=user_type,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Create JWT token
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email, "user_type": user_type}
            )
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "user_type": user.user_type,
                    "email_verified": user.email_verified
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error creating/getting user from Google: {str(e)}")
            raise AuthenticationError(f"Failed to create/get user: {str(e)}")
    
    def create_or_get_church_admin_from_google(self, google_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Create or get church admin from Google data (from google_oauth_service.py)
        Maintains API compatibility
        """
        try:
            from app.model.m_church_admin import ChurchAdmin
            from app.model.m_church import Church
            from app.utils.jwt_handler import create_access_token
            
            email = google_data.get("email")
            if not email:
                raise ValidationError("Email is required for Google OAuth")
            
            # Check if church admin already exists
            church_admin = db.query(ChurchAdmin).filter(ChurchAdmin.email == email).first()
            
            if church_admin:
                # Update church admin with Google data
                church_admin.google_id = google_data.get("sub")
                church_admin.first_name = google_data.get("given_name", church_admin.first_name)
                church_admin.last_name = google_data.get("family_name", church_admin.last_name)
                church_admin.profile_picture_url = google_data.get("picture", church_admin.profile_picture_url)
                church_admin.email_verified = google_data.get("email_verified", church_admin.email_verified)
                church_admin.updated_at = datetime.now(timezone.utc)
                
                db.commit()
            else:
                # Create new church admin
                church_admin = ChurchAdmin(
                    email=email,
                    google_id=google_data.get("sub"),
                    first_name=google_data.get("given_name", ""),
                    last_name=google_data.get("family_name", ""),
                    profile_picture_url=google_data.get("picture"),
                    email_verified=google_data.get("email_verified", False),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(church_admin)
                db.commit()
                db.refresh(church_admin)
            
            # Create JWT token
            access_token = create_access_token(
                data={"sub": str(church_admin.id), "email": church_admin.email, "user_type": "church_admin"}
            )
            
            return {
                "success": True,
                "church_admin": {
                    "id": church_admin.id,
                    "email": church_admin.email,
                    "first_name": church_admin.first_name,
                    "last_name": church_admin.last_name,
                    "email_verified": church_admin.email_verified
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error creating/getting church admin from Google: {str(e)}")
            raise AuthenticationError(f"Failed to create/get church admin: {str(e)}")

# Create service instances for backward compatibility
oauth_service = OAuthService()
google_oauth_service = OAuthService()  # Alias for backward compatibility
donor_google_oauth_service = OAuthService()  # Alias for backward compatibility