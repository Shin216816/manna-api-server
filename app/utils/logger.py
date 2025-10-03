"""
Logger Utility Module

This module provides logging functionality for the Manna Backend API.
It includes structured logging, error handling, and configuration options.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class Logger:
    """Enhanced logger with structured logging and error handling"""
    
    def __init__(self, name: str = "manna_backend", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # Set to DEBUG to show all logs
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        if kwargs:
            message = f"{message} - {json.dumps(kwargs)}"
        self.logger.info(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data"""
        if kwargs:
            message = f"{message} - {json.dumps(kwargs)}"
        self.logger.error(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data"""
        if kwargs:
            message = f"{message} - {json.dumps(kwargs)}"
        self.logger.warning(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data"""
        if kwargs:
            message = f"{message} - {json.dumps(kwargs)}"
        self.logger.debug(message)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured data"""
        if kwargs:
            message = f"{message} - {json.dumps(kwargs)}"
        self.logger.critical(message)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   response_time: float, origin: Optional[str] = None, **kwargs):
        """Log HTTP request details"""
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": f"{response_time:.3f}s",
            "origin": origin,
            "timestamp": datetime.now().isoformat()
        }
        log_data.update(kwargs)
        
        self.info(f"HTTP Request: {method} {path} - {status_code}", **log_data)
    
    def log_error(self, error: Exception, context: Optional[str] = None, **kwargs):
        """Log error with context and stack trace"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        error_data.update(kwargs)
        
        self.error(f"Error in {context or 'unknown'}: {str(error)}", **error_data)
    
    def log_cors_request(self, method: str, path: str, origin: str, 
                        user_agent: Optional[str] = None, **kwargs):
        """Log CORS request details"""
        cors_data = {
            "method": method,
            "path": path,
            "origin": origin,
            "user_agent": user_agent,
            "timestamp": datetime.now().isoformat()
        }
        cors_data.update(kwargs)
        
        self.info(f"CORS Request: {method} {path} from {origin}", **cors_data)
    
    def log_cors_error(self, error_type: str, details: str, origin: Optional[str] = None, **kwargs):
        """Log CORS error with details"""
        error_data = {
            "error_type": error_type,
            "details": details,
            "origin": origin,
            "timestamp": datetime.now().isoformat()
        }
        error_data.update(kwargs)
        
        self.error(f"CORS Error: {error_type} - {details}", **error_data)


# Create default logger instance
default_logger = Logger("manna_backend", "DEBUG")

def get_logger(name: Optional[str] = None) -> Logger:
    """Get logger instance"""
    if name:
        return Logger(name)
    return default_logger 
