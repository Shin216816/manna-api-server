from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import platform
from sqlalchemy import text

from app.core.responses import ResponseFactory


def health_check():
    """Basic health check endpoint"""
    try:
        return ResponseFactory.success(
            message="Service is healthy",
            data={
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "2.0.0",
            },
        )
    except Exception as e:

        raise HTTPException(status_code=500, detail="Service is unhealthy")


def detailed_health_check(db: Session):
    """Detailed health check with system metrics"""
    try:
        # Database health
        db_healthy = True
        try:
            db.execute(text("SELECT 1"))
        except Exception as e:
            db_healthy = False

        # System metrics (using built-in modules)
        cpu_percent = 0.0  # Not available without psutil
        memory_percent = 0.0
        memory_available = 0.0
        disk_percent = 0.0
        disk_free = 0.0
        process_memory = 0.0

        # Basic system info using built-in modules
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
        }

        return ResponseFactory.success(
            message="Detailed health check completed",
            data={
                "status": "healthy" if db_healthy else "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "2.0.0",
                "database": {"status": "healthy" if db_healthy else "unhealthy"},
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available": memory_available,  # GB
                    "disk_percent": disk_percent,
                    "disk_free": disk_free,  # GB
                    "process_memory_mb": round(process_memory, 2),
                    "platform": system_info["platform"],
                    "architecture": system_info["architecture"],
                    "processor": system_info["processor"],
                },
            },
        )
    except Exception as e:

        raise HTTPException(status_code=500, detail="Service is unhealthy")
