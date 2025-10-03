"""
Comprehensive Security Middleware for Production

Implements:
- Rate limiting for all endpoints
- Input validation and sanitization
- Security headers
- CSRF protection
- Request logging
- IP whitelisting/blacklisting
"""

import time
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import re
import json

from app.core.responses import ResponseFactory
from app.core.exceptions import MannaException

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for production"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_cache: Dict[str, Dict] = {}
        self.blocked_ips: set = set()
        self.whitelisted_ips: set = set()
        self.csrf_tokens: Dict[str, str] = {}
        
        # Rate limiting configuration
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 60},      # 10 auth attempts per minute
            'api': {'requests': 1000, 'window': 3600},   # 1000 API calls per hour
            'donation': {'requests': 20, 'window': 60},  # 20 donations per minute
        }
        
        # Security headers
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; font-src 'self' data:; connect-src 'self' https://api.plaid.com https://api.stripe.com;"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID for tracking
        request_id = secrets.token_hex(8)
        request.state.request_id = request_id
        
        try:
            # Security checks
            await self._perform_security_checks(request)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log request
            self._log_request(request, response)
            
            return response
            
        except SecurityException as e:
            return self._create_security_error_response(e, request_id)
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return self._create_security_error_response(
                SecurityException("Internal security error", "INTERNAL_ERROR"), 
                request_id
            )
    
    async def _perform_security_checks(self, request: Request):
        """Perform all security checks"""
        
        # 1. IP-based security
        await self._check_ip_security(request)
        
        # 2. Rate limiting
        await self._check_rate_limits(request)
        
        # 3. Input validation
        await self._validate_input(request)
        
        # 4. CSRF protection for state-changing operations
        await self._check_csrf_protection(request)
        
        # 5. Request size limits
        await self._check_request_size(request)
    
    async def _check_ip_security(self, request: Request):
        """Check IP whitelist/blacklist"""
        client_ip = self._get_client_ip(request)
        
        if client_ip in self.blocked_ips:
            raise SecurityException("IP address is blocked", "IP_BLOCKED")
        
        # Check whitelist if configured
        if self.whitelisted_ips and client_ip not in self.whitelisted_ips:
            raise SecurityException("IP address not whitelisted", "IP_NOT_WHITELISTED")
    
    async def _check_rate_limits(self, request: Request):
        """Check rate limits based on endpoint and user"""
        client_id = self._get_client_identifier(request)
        endpoint = request.url.path
        method = request.method
        
        # Determine rate limit type
        limit_type = self._get_rate_limit_type(endpoint, method)
        
        # Check if rate limited
        is_limited, rate_info = self._is_rate_limited(client_id, endpoint, limit_type)
        
        if is_limited:
            raise SecurityException(
                f"Rate limit exceeded. Try again in {rate_info['retry_after']} seconds",
                "RATE_LIMIT_EXCEEDED",
                {"retry_after": rate_info['retry_after']}
            )
    
    async def _validate_input(self, request: Request):
        """Validate and sanitize input data"""
        
        # Check for malicious patterns in URL
        if self._contains_malicious_patterns(request.url.path):
            raise SecurityException("Malicious pattern detected in URL", "MALICIOUS_INPUT")
        
        # Check query parameters
        for param, value in request.query_params.items():
            if self._contains_malicious_patterns(str(value)):
                raise SecurityException(f"Malicious pattern in parameter: {param}", "MALICIOUS_INPUT")
        
        # Check request body for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    # Check for SQL injection patterns
                    if self._contains_sql_injection(str(body)):
                        raise SecurityException("SQL injection pattern detected", "MALICIOUS_INPUT")
                    
                    # Check for XSS patterns
                    if self._contains_xss_patterns(str(body)):
                        raise SecurityException("XSS pattern detected", "MALICIOUS_INPUT")
            except Exception as e:
                logger.warning(f"Error validating request body: {e}")
    
    async def _check_csrf_protection(self, request: Request):
        """Check CSRF protection for state-changing operations"""
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Skip CSRF check for API endpoints with proper authentication
            if request.url.path.startswith('/api/v1/') and request.headers.get('authorization'):
                return
            
            # Check CSRF token
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                raise SecurityException("CSRF token required", "CSRF_TOKEN_MISSING")
            
            # Validate CSRF token
            if not self._validate_csrf_token(csrf_token, request):
                raise SecurityException("Invalid CSRF token", "CSRF_TOKEN_INVALID")
    
    async def _check_request_size(self, request: Request):
        """Check request size limits"""
        content_length = request.headers.get('content-length')
        if content_length:
            size = int(content_length)
            max_size = 10 * 1024 * 1024  # 10MB limit
            
            if size > max_size:
                raise SecurityException("Request too large", "REQUEST_TOO_LARGE")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        client_ip = self._get_client_ip(request)
        
        # Add user ID if authenticated
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"{client_ip}:{user_id}"
        
        return client_ip
    
    def _get_rate_limit_type(self, endpoint: str, method: str) -> str:
        """Determine rate limit type based on endpoint"""
        if '/auth/' in endpoint or '/login' in endpoint:
            return 'auth'
        elif '/donation' in endpoint or '/roundup' in endpoint:
            return 'donation'
        elif endpoint.startswith('/api/v1/'):
            return 'api'
        else:
            return 'default'
    
    def _is_rate_limited(self, client_id: str, endpoint: str, limit_type: str) -> Tuple[bool, Dict]:
        """Check if client is rate limited"""
        current_time = time.time()
        window = self.rate_limits[limit_type]['window']
        max_requests = self.rate_limits[limit_type]['requests']
        
        key = f"{client_id}:{endpoint}:{limit_type}"
        
        # Clean old entries
        if key in self.rate_limit_cache:
            self.rate_limit_cache[key] = [
                req_time for req_time in self.rate_limit_cache[key]
                if current_time - req_time < window
            ]
        else:
            self.rate_limit_cache[key] = []
        
        # Check if limit exceeded
        if len(self.rate_limit_cache[key]) >= max_requests:
            oldest_request = min(self.rate_limit_cache[key])
            retry_after = int(window - (current_time - oldest_request)) + 1
            
            return True, {
                'retry_after': retry_after,
                'limit': max_requests,
                'window': window,
                'current_requests': len(self.rate_limit_cache[key])
            }
        
        # Add current request
        self.rate_limit_cache[key].append(current_time)
        
        return False, {}
    
    def _contains_malicious_patterns(self, text: str) -> bool:
        """Check for malicious patterns in text"""
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'\.\./',  # Directory traversal
            r'\.\.\\',  # Windows directory traversal
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'execute\s*\(',
            r'--',
            r'/\*.*?\*/',
            r';\s*drop',
            r';\s*delete',
            r';\s*insert',
            r';\s*update',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_xss_patterns(self, text: str) -> bool:
        """Check for XSS patterns"""
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token"""
        # Get session ID from request
        session_id = request.cookies.get('session_id')
        if not session_id:
            return False
        
        # Check if token exists and matches
        expected_token = self.csrf_tokens.get(session_id)
        if not expected_token or expected_token != token:
            return False
        
        # Check token age (max 1 hour)
        token_time = self.csrf_tokens.get(f"{session_id}_time")
        if token_time and time.time() - token_time > 3600:
            del self.csrf_tokens[session_id]
            del self.csrf_tokens[f"{session_id}_time"]
            return False
        
        return True
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _log_request(self, request: Request, response: Response):
        """Log security-relevant requests"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'client_ip': client_ip,
            'user_id': user_id,
            'method': request.method,
            'url': str(request.url),
            'status_code': response.status_code,
            'user_agent': request.headers.get('user-agent', ''),
            'referer': request.headers.get('referer', ''),
        }
        
        # Log suspicious activity
        if response.status_code >= 400:
            logger.warning(f"Security event: {log_data}")
        else:
            logger.info(f"Request: {log_data}")
    
    def _create_security_error_response(self, error: 'SecurityException', request_id: str) -> JSONResponse:
        """Create standardized security error response"""
        error_response = ResponseFactory.error(
            message=error.message,
            error_code=error.error_code,
            details=error.details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=200,  # Always return 200 for consistency
            content=error_response.model_dump(mode='json')
        )


class SecurityException(MannaException):
    """Custom security exception"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        super().__init__(message, error_code, details)


def generate_csrf_token(session_id: str) -> str:
    """Generate CSRF token for session"""
    token = secrets.token_urlsafe(32)
    security_middleware = SecurityMiddleware(None)  # This should be properly injected
    security_middleware.csrf_tokens[session_id] = token
    security_middleware.csrf_tokens[f"{session_id}_time"] = time.time()
    return token


def setup_security_middleware(app):
    """Setup security middleware for the application"""
    app.add_middleware(SecurityMiddleware)
