"""
Monitoring Middleware for Production

Tracks:
- Request/response times
- Error rates
- API usage patterns
- Performance metrics
- User activity
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking application metrics"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.monitoring_service = get_monitoring_service()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Track request
        self.request_count += 1
        
        # Get request context
        request_context = self._get_request_context(request)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Track successful request
            self.monitoring_service.track_request(request, response_time, response.status_code)
            
            # Add monitoring headers
            self._add_monitoring_headers(response, response_time)
            
            return response
            
        except Exception as e:
            # Track error
            self.error_count += 1
            response_time = time.time() - start_time
            
            # Track error in monitoring service
            self.monitoring_service.track_error(e, request_context)
            
            # Re-raise the exception
            raise
    
    def _get_request_context(self, request: Request) -> Dict[str, Any]:
        """Extract request context for monitoring"""
        return {
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent', ''),
            'referer': request.headers.get('referer', ''),
            'user_id': getattr(request.state, 'user_id', None),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _add_monitoring_headers(self, response: Response, response_time: float):
        """Add monitoring headers to response"""
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        response.headers['X-Request-Count'] = str(self.request_count)
        response.headers['X-Error-Count'] = str(self.error_count)
        
        if self.request_count > 0:
            avg_response_time = self.total_response_time / self.request_count
            response.headers['X-Avg-Response-Time'] = f"{avg_response_time:.3f}s"
        
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100
            response.headers['X-Error-Rate'] = f"{error_rate:.2f}%"


def setup_monitoring_middleware(app):
    """Setup monitoring middleware"""
    app.add_middleware(MonitoringMiddleware)
