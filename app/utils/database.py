import databases
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import config
import logging

# Configure logging


def create_database_engine():
    """Create database engine with NeonDB optimized settings"""
    try:
        # Get database URL from config
        database_url = config.get_database_url
        
        # Engine configuration optimized for NeonDB
        engine = create_engine(
            database_url,
            pool_size=config.DB_POOL_SIZE,  # Use config values
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_timeout=config.DB_POOL_TIMEOUT,
            pool_recycle=config.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before use
            echo=False,  # Set to True for SQL debugging
            # SSL settings for NeonDB
            connect_args={
                "sslmode": "require",
                "application_name": "manna_backend"
            } if "neon.tech" in database_url else {}
        )
        
        return engine
        
    except Exception as e:
        raise

# Create engine
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database instance for async operations
database = databases.Database(config.get_database_url)

from contextlib import contextmanager

@contextmanager
def db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            yield db
    except Exception as e:
        raise

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Async dependency for FastAPI to get database session"""
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()

def test_database_connection():
    """Test database connection and return status"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        raise
