"""
Test Configuration and Fixtures

Provides:
- Test database setup
- Authentication fixtures
- Mock services
- Test utilities
- Coverage configuration
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.utils.database import get_db, Base
from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.core.config import settings

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone="+1234567890",
        is_active=True,
        role="donor"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_church(db_session) -> Church:
    """Create a test church."""
    church = Church(
        name="Test Church",
        email="church@example.com",
        phone="+1234567890",
        address="123 Test St",
        city="Test City",
        state="TS",
        zip_code="12345",
        is_active=True
    )
    db_session.add(church)
    db_session.commit()
    db_session.refresh(church)
    return church

@pytest.fixture
def test_church_admin(db_session, test_user, test_church) -> ChurchAdmin:
    """Create a test church admin."""
    church_admin = ChurchAdmin(
        user_id=test_user.id,
        church_id=test_church.id,
        is_active=True
    )
    db_session.add(church_admin)
    db_session.commit()
    db_session.refresh(church_admin)
    return church_admin

@pytest.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers for test user."""
    # This would normally create a JWT token
    # For testing, we'll use a mock token
    return {"Authorization": f"Bearer test_token_{test_user.id}"}

@pytest.fixture
def mock_plaid_service():
    """Mock Plaid service for testing."""
    class MockPlaidService:
        def create_link_token(self, user_id: int):
            return {"link_token": "test_link_token", "expiration": "2024-12-31T23:59:59Z"}
        
        def exchange_public_token(self, public_token: str):
            return {"access_token": "test_access_token", "item_id": "test_item_id"}
        
        def get_accounts(self, access_token: str):
            return {
                "accounts": [
                    {
                        "account_id": "test_account_id",
                        "name": "Test Account",
                        "type": "depository",
                        "mask": "0000",
                        "balances": {"available": 1000.0, "current": 1000.0}
                    }
                ]
            }
        
        def get_transactions(self, access_token: str, start_date: str, end_date: str):
            return {
                "transactions": [
                    {
                        "transaction_id": "test_transaction_id",
                        "account_id": "test_account_id",
                        "amount": -25.50,
                        "date": "2024-01-15",
                        "name": "Test Purchase",
                        "merchant_name": "Test Store",
                        "category": ["shopping"],
                        "pending": False
                    }
                ]
            }
    
    return MockPlaidService()

@pytest.fixture
def mock_stripe_service():
    """Mock Stripe service for testing."""
    class MockStripeService:
        def create_customer(self, email: str, name: str):
            return {"id": "cus_test123", "email": email, "name": name}
        
        def create_payment_method(self, customer_id: str, payment_method_id: str):
            return {"id": "pm_test123", "customer": customer_id}
        
        def create_payment_intent(self, amount: int, currency: str, customer_id: str):
            return {
                "id": "pi_test123",
                "amount": amount,
                "currency": currency,
                "customer": customer_id,
                "status": "succeeded"
            }
        
        def create_transfer(self, amount: int, destination: str):
            return {
                "id": "tr_test123",
                "amount": amount,
                "destination": destination,
                "status": "succeeded"
            }
    
    return MockStripeService()

@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    class MockNotificationService:
        def __init__(self):
            self.sent_notifications = []
        
        async def send_notification(self, user_id: int, template_name: str, data: Dict[str, Any]):
            self.sent_notifications.append({
                "user_id": user_id,
                "template_name": template_name,
                "data": data
            })
            return True
        
        def get_sent_notifications(self):
            return self.sent_notifications
        
        def clear_notifications(self):
            self.sent_notifications.clear()
    
    return MockNotificationService()

@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    class MockCacheService:
        def __init__(self):
            self.cache = {}
        
        def get(self, key: str, default: Any = None):
            return self.cache.get(key, default)
        
        def set(self, key: str, value: Any, ttl: int = None):
            self.cache[key] = value
            return True
        
        def delete(self, key: str):
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        
        def clear(self, pattern: str = None):
            if pattern:
                keys_to_delete = [k for k in self.cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.cache[key]
                return len(keys_to_delete)
            else:
                count = len(self.cache)
                self.cache.clear()
                return count
    
    return MockCacheService()

@pytest.fixture
def test_data():
    """Provide test data for various scenarios."""
    return {
        "user_data": {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890",
            "password": "testpassword123"
        },
        "church_data": {
            "name": "Test Church",
            "email": "church@example.com",
            "phone": "+1234567890",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345"
        },
        "donation_data": {
            "amount": 25.50,
            "type": "roundup",
            "description": "Test donation"
        },
        "roundup_settings": {
            "frequency": "biweekly",
            "multiplier": "2x",
            "pause": False,
            "cover_processing_fees": True,
            "monthly_cap": 100.0
        }
    }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add unit marker to tests in unit directory
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration directory
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to tests in e2e directory
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
