"""
Enhanced CORS Error Handling Utility

This module provides comprehensive CORS error handling, logging, and debugging
capabilities for the Manna Backend API.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.config import config

class CORSHandler:
    """Enhanced CORS error handling and logging utility"""
    
    def __init__(self):
        self.error_count = 0
        self.request_count = 0
        
    def log_cors_request(self, request: Request, response: Optional[Response] = None):
        """Log CORS request details for debugging"""
        if not config.CORS_LOG_REQUESTS:
            return
            
        self.request_count += 1
        
        origin = request.headers.get("origin", "unknown")
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": self.request_count,
            "method": method,
            "path": path,
            "origin": origin,
            "user_agent": user_agent,
            "status_code": response.status_code if response else None,
            "cors_allowed": self._is_origin_allowed(origin)
        }
        
        self.info(f"CORS Request: {json.dumps(log_data, indent=2)}")
    
    def log_cors_error(self, error_type: str, details: str, request: Optional[Request] = None):
        """Log CORS error with detailed information"""
        self.error_count += 1
        
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_id": self.error_count,
            "error_type": error_type,
            "details": details,
            "request_info": self._get_request_info(request) if request else None
        }
        
        self.error(f"CORS Error: {json.dumps(error_data, indent=2)}")
    
    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract request information for logging"""
        return {
            "method": request.method,
            "path": request.url.path,
            "origin": request.headers.get("origin"),
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "host": request.headers.get("host")
        }
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed based on configuration and environment"""
        if not origin:
            return False
        
        # In development, allow all origins
        if config.IS_DEVELOPMENT or config.ENVIRONMENT in ['development', 'local', 'test']:
            return True
        
        # Production origin checking
        allowed_origins = config.CORS_ORIGINS
        return "*" in allowed_origins or origin in allowed_origins
    
    def _is_method_allowed(self, method: str) -> bool:
        """Check if HTTP method is allowed"""
        allowed_methods = config.CORS_METHODS
        return method.upper() in [m.upper() for m in allowed_methods]
    
    def _are_headers_allowed(self, headers: str) -> bool:
        """Check if requested headers are allowed"""
        if not headers:
            return True
        
        allowed_headers = [h.lower() for h in config.CORS_HEADERS]
        requested_headers = [h.strip().lower() for h in headers.split(",")]
        
        return all(header in allowed_headers for header in requested_headers)
    
    def validate_cors_request(self, request: Request) -> Dict[str, Any]:
        """Validate CORS request and return validation results"""
        origin = request.headers.get("origin", "")
        method = request.method
        headers = request.headers.get("access-control-request-headers", "")
        
        errors: List[str] = []
        warnings: List[str] = []
        
        validation_result: Dict[str, Any] = {
            "is_valid": True,
            "errors": errors,
            "warnings": warnings,
            "origin_allowed": self._is_origin_allowed(origin),
            "method_allowed": self._is_method_allowed(method),
            "headers_allowed": self._are_headers_allowed(headers)
        }
        
        # Check origin
        if not validation_result["origin_allowed"]:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Origin '{origin}' not allowed")
        
        # Check method
        if not validation_result["method_allowed"]:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Method '{method}' not allowed")
        
        # Check headers
        if not validation_result["headers_allowed"]:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Headers '{headers}' not allowed")
        
        # Add warnings for debugging
        if not origin:
            validation_result["warnings"].append("No origin header provided")
        
        return validation_result
    
    def create_cors_error_response(self, error_type: str, details: str, status_code: int = 400) -> JSONResponse:
        """Create standardized CORS error response with environment-aware information"""
        # Base error response
        error_response: Dict[str, Any] = {
            "success": False,
            "error": "CORS_ERROR",
            "error_type": error_type,
            "details": details,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add help information based on environment
        if config.IS_DEVELOPMENT or config.ENVIRONMENT in ['development', 'local', 'test']:
            # Full debugging info in development
            error_response["help"] = {
                "documentation": "https://docs.manna.com/cors",
                "contact": "support@manna.com",
                "environment": config.ENVIRONMENT,
                "debug_info": {
                    "allowed_origins": config.CORS_ORIGINS,
                    "allowed_methods": config.CORS_METHODS,
                    "allowed_headers": config.CORS_HEADERS,
                    "credentials_allowed": config.CORS_ALLOW_CREDENTIALS,
                    "max_age": config.CORS_MAX_AGE
                },
                "tips": [
                    "Check if your origin is in the allowed list",
                    "Ensure you're using the correct HTTP method",
                    "Verify required headers are included"
                ]
            }
        else:
            # Minimal info in production
            error_response["help"] = {
                "documentation": "https://docs.manna.com/cors",
                "contact": "support@manna.com"
            }
        
        # Set CORS headers based on environment
        cors_headers = {}
        if config.IS_DEVELOPMENT or config.ENVIRONMENT in ['development', 'local', 'test']:
            # Permissive headers for development
            cors_headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": ", ".join(config.CORS_METHODS),
                "Access-Control-Allow-Headers": ", ".join(config.CORS_HEADERS),
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": str(config.CORS_MAX_AGE)
            }
        else:
            # Restricted headers for production
            cors_headers = {
                "Access-Control-Allow-Origin": "null",  # No permissive origin in production errors
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600"
            }
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers=cors_headers
        )
    
    def get_cors_headers(self, origin: str) -> Dict[str, str]:
        """Get appropriate CORS headers for response based on environment"""
        headers = {}
        
        # Handle origin based on environment
        if config.IS_DEVELOPMENT or config.ENVIRONMENT in ['development', 'local', 'test']:
            # Allow all origins in development
            if origin and origin != "null":
                headers["Access-Control-Allow-Origin"] = origin
            else:
                headers["Access-Control-Allow-Origin"] = "*"
        else:
            # Strict origin checking in production
            if self._is_origin_allowed(origin):
                headers["Access-Control-Allow-Origin"] = origin
            else:
                headers["Access-Control-Allow-Origin"] = "null"
        
        # Set other headers based on environment
        if config.IS_DEVELOPMENT or config.ENVIRONMENT in ['development', 'local', 'test']:
            headers.update({
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": ", ".join(config.CORS_METHODS),
                "Access-Control-Allow-Headers": ", ".join(config.CORS_HEADERS),
                "Access-Control-Expose-Headers": ", ".join(config.CORS_EXPOSE_HEADERS),
                "Access-Control-Max-Age": str(config.CORS_MAX_AGE)
            })
        else:
            headers.update({
                "Access-Control-Allow-Credentials": str(config.CORS_ALLOW_CREDENTIALS).lower(),
                "Access-Control-Allow-Methods": ", ".join(config.CORS_METHODS),
                "Access-Control-Allow-Headers": ", ".join(config.CORS_HEADERS),
                "Access-Control-Expose-Headers": ", ".join(config.CORS_EXPOSE_HEADERS),
                "Access-Control-Max-Age": str(config.CORS_MAX_AGE)
            })
        
        return headers
    
    def get_cors_statistics(self) -> Dict[str, Any]:
        """Get CORS statistics for monitoring"""
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            "cors_enabled": True,
            "debug_mode": config.CORS_DEBUG,
            "logging_enabled": config.CORS_LOG_REQUESTS,
            "health_check_enabled": config.CORS_HEALTH_CHECK_ENABLED
        }
    
    def handle_cors_preflight(self, request: Request) -> JSONResponse:
        """Handle CORS preflight requests with comprehensive validation"""
        try:
            # Log the preflight request
            self.log_cors_request(request)
            
            # Validate the request
            validation = self.validate_cors_request(request)
            
            if not validation["is_valid"]:
                # Log the error
                self.log_cors_error("PREFLIGHT_VALIDATION_FAILED", str(validation["errors"]), request)
                
                # Return appropriate error response
                if not validation["origin_allowed"]:
                    return self.create_cors_error_response(
                        "ORIGIN_NOT_ALLOWED",
                        f"Origin '{request.headers.get('origin', 'unknown')}' is not allowed",
                        403
                    )
                elif not validation["method_allowed"]:
                    return self.create_cors_error_response(
                        "METHOD_NOT_ALLOWED",
                        f"Method '{request.method}' is not allowed",
                        405
                    )
                else:
                    return self.create_cors_error_response(
                        "HEADERS_NOT_ALLOWED",
                        f"Headers '{request.headers.get('access-control-request-headers', '')}' are not allowed",
                        400
                    )
            
            # Return successful preflight response
            origin = request.headers.get("origin", "*")
            headers = self.get_cors_headers(origin)
            
            return JSONResponse(
                status_code=200,
                content={"message": "CORS preflight successful"},
                headers=headers
            )
            
        except Exception as e:
            self.log_cors_error("PREFLIGHT_INTERNAL_ERROR", str(e), request)
            return self.create_cors_error_response(
                "INTERNAL_ERROR",
                "Internal CORS processing error",
                500
            )
    
    def handle_cors_error(self, request: Request, error: Exception) -> JSONResponse:
        """Handle CORS errors with detailed logging and response"""
        error_type = type(error).__name__
        error_details = str(error)
        
        # Log the error
        self.log_cors_error(error_type, error_details, request)
        
        # Create appropriate error response
        if "origin" in error_details.lower():
            return self.create_cors_error_response(
                "ORIGIN_ERROR",
                error_details,
                403
            )
        elif "method" in error_details.lower():
            return self.create_cors_error_response(
                "METHOD_ERROR",
                error_details,
                405
            )
        elif "header" in error_details.lower():
            return self.create_cors_error_response(
                "HEADER_ERROR",
                error_details,
                400
            )
        else:
            return self.create_cors_error_response(
                "GENERAL_CORS_ERROR",
                error_details,
                500
            )

# Create global CORS handler instance
cors_handler = CORSHandler()

def get_cors_handler() -> CORSHandler:
    """Get the global CORS handler instance"""
    return cors_handler 
