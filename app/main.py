import os
import sys
from datetime import datetime
from typing import Callable, cast, Any
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.constants import get_auth_constant, get_business_constant
from app.utils.logger import Logger, get_logger
from app.middleware.exception_handler import setup_global_exception_handler
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to DEBUG level
logging.getLogger("app").setLevel(logging.DEBUG)
logging.getLogger("app.services.plaid_client").setLevel(logging.DEBUG)
logging.getLogger("app.controller.donor.transactions").setLevel(logging.DEBUG)

# Initialize logger
logger = get_logger("main")

def custom_rate_limit_handler(request, exc):
    """Enhanced rate limit handler with consistent response format"""
    request_id = getattr(request.state, 'request_id', None)
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Rate limit exceeded. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "details": {
                "retry_after": getattr(exc, 'retry_after', 60),
                "limit": getattr(exc, 'detail', {}).get('limit', 'Unknown')
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
    )

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app with comprehensive documentation
app = FastAPI(
    title="Manna API",
    description="""
A comprehensive church donation management system that enables seamless roundup donations, 
church administration, and donor management. Built for modern churches and communities.

## Key Features
- Roundup donation processing
- Church administration tools
- Donor management and analytics
- Payment processing integration
- Mobile app support
- Real-time notifications

## Authentication
Most endpoints require authentication via JWT tokens. Include the token in the Authorization header as 'Bearer {token}'.

## Rate Limiting
API requests are rate limited to ensure fair usage. Check response headers for rate limit information.
""",
    version="2.0.0",
    contact={
        "name": "Manna API Support",
        "email": "support@manna.com",
        "url": "https://docs.manna.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication, registration, and account management"
        },
        {
            "name": "Donor",
            "description": "Donor-specific endpoints for donations, settings, and account management"
        },
        {
            "name": "Church Admin",
            "description": "Church administration tools for managing donations, members, and analytics"
        },
        {
            "name": "Platform Admin",
            "description": "Platform administration and system management"
        },
        {
            "name": "Mobile",
            "description": "Mobile app optimized endpoints"
        },
        {
            "name": "System",
            "description": "Health checks, monitoring, and system status"
        }
    ],
    servers=[
        {"url": "http://localhost:8000", "description": "Development Server"},
        {"url": "http://127.0.0.1:8000", "description": "Development Server (IP)"},
        {"url": "https://manna-api-server.onrender.com", "description": "Production Server"},
        {"url": "https://staging-api.manna.com", "description": "Staging Server"}
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        "requestInterceptor": "(req) => { req.headers['Access-Control-Allow-Origin'] = '*'; return req; }",
        "responseInterceptor": "(res) => { return res; }",
        "onComplete": "() => { console.log('Swagger UI loaded with CORS support'); }",
        "validatorUrl": None,  # Disable validator to prevent external requests
        "docExpansion": "none",
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True
    }
)

# Add rate limiting
app.state.limiter = limiter
if os.getenv("TESTING") != "true":
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Add CORS middleware FIRST (before exception handler)
def get_cors_origins():
    """Get CORS origins based on environment"""
    from app.config import config
    if config.ENVIRONMENT == "production":
        return [
            "https://manna-api-server.onrender.com",
            "https://docs.manna.com",
            "https://swagger.io",
            "https://editor.swagger.io",
            # Mobile app origins
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:4200",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:4200"
        ]
    elif config.ENVIRONMENT == "staging":
        return [
            "https://staging-api.manna.com",
            "https://staging.manna.com",
            "https://swagger.io",
            "https://editor.swagger.io",
            # Mobile app origins
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:4200",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:4200",
            "*"
        ]
    else:  # development - allow common local dev origins explicitly (credentials safe)
        return [
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:4200",
            "http://127.0.0.1:4200"
        ]

# Enhanced CORS middleware with comprehensive error handling
# Note: Using Middleware class to avoid type compatibility issues
app.add_middleware(
    cast(Any, CORSMiddleware),
    allow_origins=get_cors_origins(),
    allow_origin_regex=r"^https?:\/\/localhost:(5173|3000|8080|4200)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "X-API-Key",
        "X-Client-Version",
        "User-Agent",
        "Cache-Control",
        "Pragma",
        "Expires"
    ],
    expose_headers=[
        "Content-Length",
        "Content-Type",
        "X-Total-Count", 
        "X-Page-Count",
        "Access-Control-Allow-Origin"
    ],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Additional CORS middleware to ensure headers are always present
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add CORS headers for all responses
    origin = request.headers.get("origin")
    if origin and origin.startswith("http://localhost:"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, X-API-Key, X-Client-Version, User-Agent, Cache-Control, Pragma, Expires"
        response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Type, X-Total-Count, X-Page-Count"
        response.headers["Vary"] = "Origin"
    
    # Add basic security headers for development
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; font-src 'self' data:; connect-src 'self' http://localhost:* https://api.plaid.com https://api.stripe.com;"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Setup comprehensive global exception handler AFTER CORS middleware
# This must be called before including routers to ensure all exceptions are caught
setup_global_exception_handler(app)

# Add debugging for exception handler setup


# Import models to ensure they're registered with SQLAlchemy
from app.model import *

# Import and mount routers
from app.router.v1 import v1_router

# Add global OPTIONS handler for CORS preflight
@app.options("/{path:path}")
async def options_handler(request: Request):
    """Handle all OPTIONS requests for CORS preflight"""
    origin = request.headers.get("origin", "*")
    
    # Only allow localhost origins for security
    if origin and not origin.startswith("http://localhost:") and not origin.startswith("http://127.0.0.1:"):
        origin = "http://localhost:5173"  # Default to frontend origin
    
    return JSONResponse(
        content="OK",
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, X-API-Key, X-Client-Version, User-Agent, Cache-Control, Pragma, Expires",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Expose-Headers": "Content-Length, Content-Type, X-Total-Count, X-Page-Count",
            "Access-Control-Max-Age": "86400",
            "Vary": "Origin"
        }
    )

# Mount API routes
app.include_router(v1_router, prefix="/api/v1")



# Mount static files for uploaded content
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    API Health Check
    
    Returns the current health status of the Manna API.
    Useful for monitoring, load balancers, and system health checks.
    
    **Response:**
    - **status**: Current API status (healthy/unhealthy)
    - **message**: Status description
    - **version**: Current API version
    - **timestamp**: Current server time
    - **uptime**: Server uptime information
    - **environment**: Current environment (production/staging/development)
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "message": "Manna API is running",
        "version": "2.0.0",
        "timestamp": "2024-01-15T10:30:00Z",
        "uptime": "2 days, 3 hours, 45 minutes",
        "environment": "production"
    }
    ```
    """
    from app.config import config
    
    return {
        "status": "healthy", 
        "message": "Manna API is running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": config.ENVIRONMENT,
        "uptime": "N/A"  # Uptime calculation would be implemented in production
    }

# Database health check endpoint
@app.get("/db", tags=["System"])
async def database_health_check():
    """
    Database Health Check
    
    Tests the database connection and returns detailed status information.
    Useful for monitoring database connectivity and performance.
    
    **Response:**
    - **status**: Database connection status (connected/disconnected/error)
    - **message**: Status description
    - **database_info**: Database details (name, version, ssl status, provider)
    - **connection_pool**: Connection pool statistics
    - **performance**: Database performance metrics
    - **timestamp**: Current server time
    
    **Example Response:**
    ```json
    {
        "status": "connected",
        "message": "Database connection successful",
        "database_info": {
            "name": "neondb",
            "version": "PostgreSQL 15.4",
            "ssl_enabled": true,
            "provider": "NeonDB"
        },
        "connection_pool": {
            "pool_size": 10,
            "max_overflow": 20,
            "checked_out": 2,
            "overflow": 0,
            "pool_timeout": 30,
            "pool_recycle": 3600
        },
        "performance": {
            "response_time": "15ms",
            "active_connections": 2,
            "idle_connections": 8
        },
        "timestamp": "2024-01-15T10:30:00Z"
    }
    ```
    """
    try:
        from app.utils.database import engine, test_database_connection
        from app.config import config
        from sqlalchemy import text
        
        # Test connection
        if not test_database_connection():
            return {
                "status": "disconnected",
                "message": "Database connection failed",
                "database_info": None,
                "connection_pool": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get database info
        with engine.connect() as connection:
            # Get database name
            result = connection.execute(text("SELECT current_database()"))
            db_name_row = result.fetchone()
            db_name = db_name_row[0] if db_name_row else "unknown"
            
            # Get database version
            result = connection.execute(text("SELECT version()"))
            db_version_row = result.fetchone()
            db_version = db_version_row[0] if db_version_row else "unknown"
            
            # Check SSL status (for NeonDB)
            ssl_enabled = False
            if config.DATABASE_URL and "neon.tech" in config.DATABASE_URL:
                try:
                    result = connection.execute(text("SHOW ssl"))
                    ssl_row = result.fetchone()
                    ssl_status = ssl_row[0] if ssl_row else "off"
                    ssl_enabled = ssl_status == "on"
                except:
                    ssl_enabled = True  # Assume SSL for NeonDB
            
            # Get connection pool info
            pool_info = {
                "pool_size": config.DB_POOL_SIZE,
                "max_overflow": config.DB_MAX_OVERFLOW,
                "pool_timeout": config.DB_POOL_TIMEOUT,
                "pool_recycle": config.DB_POOL_RECYCLE
            }
        
        return {
            "status": "connected",
            "message": "Database connection successful",
            "database_info": {
                "name": db_name,
                "version": db_version,
                "ssl_enabled": ssl_enabled,
                "provider": "NeonDB" if config.DATABASE_URL and "neon.tech" in config.DATABASE_URL else "PostgreSQL"
            },
            "connection_pool": pool_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database health check failed: {str(e)}",
            "database_info": None,
            "connection_pool": None,
            "timestamp": datetime.now().isoformat()
        }


# Favicon endpoint (to prevent 405 errors)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint to prevent 405 errors"""
    return JSONResponse(status_code=204, content={})

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    API Root Endpoint
    
    Welcome endpoint with comprehensive API information and documentation links.
    Provides an overview of available features, endpoints, and integration guides.
    
    **Response:**
    - **message**: Welcome message
    - **version**: Current API version
    - **status**: API status
    - **docs**: Link to Swagger documentation
    - **redoc**: Link to ReDoc documentation
    - **health**: Link to health check endpoint
    - **features**: List of main API features
    - **endpoints**: Available API endpoint categories
    - **support**: Support and contact information
    
    **Example Response:**
    ```json
    {
        "message": "Welcome to Manna API - Church Donation Management System",
        "version": "2.0.0",
        "status": "healthy",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "features": [
            "User Authentication",
            "Banking Integration",
            "Church Management",
            "Admin Panel",
            "Payment Processing",
            "Analytics & Reporting",
            "Webhook Integration"
        ],
        "endpoints": {
            "mobile": "/api/v1/mobile",
            "church": "/api/v1/church",
            "admin": "/api/v1/admin",
            "shared": "/api/v1/shared"
        },
        "support": {
            "email": "support@manna.com",
            "documentation": "https://docs.manna.com",
            "status": "https://status.manna.com"
        }
    }
    ```
    """
    return {
        "message": "Welcome to Manna API - Church Donation Management System",
        "version": "2.0.0",
        "status": "healthy",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "features": [
            "User Authentication",
            "Banking Integration", 
            "Church Management",
            "Admin Panel",
            "Payment Processing",
            "Analytics & Reporting",
            "Webhook Integration"
        ],
        "endpoints": {
            "mobile": "/api/v1/mobile",
            "church": "/api/v1/church",
            "admin": "/api/v1/admin",
            "shared": "/api/v1/shared"
        },
        "support": {
            "email": "support@manna.com",
            "documentation": "https://docs.manna.com",
            "status": "https://status.manna.com"
        }
    }