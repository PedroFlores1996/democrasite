import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db, Base
from app.db.models import User, Topic, Vote, TopicAccess
from app.auth.utils import get_password_hash, create_access_token
from main import app

# Test database - use in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    # Create tables for each test
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as client:
        yield client
    
    # Clean up after each test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        email_verified=True  # Skip email verification for tests
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get auth headers with valid token"""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_topic_data():
    """Sample topic data for testing"""
    return {
        "title": "Test Topic",
        "answers": ["Option A", "Option B", "Option C"],
        "is_public": True
    }


@pytest.fixture
def private_topic_data():
    """Sample private topic data for testing"""
    return {
        "title": "Private Test Topic",
        "answers": ["Yes", "No"],
        "is_public": False,
        "allowed_users": ["testuser"]
    }


def create_verified_test_user(db, username: str, email: str, password: str = "testpass123"):
    """Helper function to create a verified user for testing"""
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        email_verified=True  # Skip email verification for tests
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user