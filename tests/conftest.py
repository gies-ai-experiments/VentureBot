"""Shared pytest fixtures for VentureBot integration tests.

This module provides fixtures for testing the full VentureBot stack
with Python 3.11 and all dependencies installed.
"""

from __future__ import annotations

import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch, AsyncMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from services.api_gateway.app.main import app
from services.api_gateway.app.database import Base, get_session
from services.api_gateway.app.models import MessageRole, JourneyStage


# Create in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a test database session with transaction rollback."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables fresh for each test
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Clean up tables after test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)


@pytest.fixture
def override_get_session(db_session: Session):
    """Override the get_session dependency for testing."""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


@pytest.fixture
async def async_client(override_get_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for FastAPI with mocked orchestrator."""
    app.dependency_overrides[get_session] = override_get_session
    
    # Mock the orchestrator to avoid real AI calls
    with patch("services.api_gateway.app.routers.chat.run_onboarding") as mock_onboard, \
         patch("services.api_gateway.app.routers.chat.generate_assistant_reply") as mock_gen:
        
        # Setup mock returns
        async def mock_run_onboarding(*args, **kwargs):
            return (
                "Welcome to VentureBot! 🚀 I'm your AI entrepreneurship coach. "
                "Let's explore your venture ideas together. What's your name?",
                JourneyStage.ONBOARDING.value,
                '{"stage": "onboarding"}'
            )
        
        async def mock_generate_reply(*args, **kwargs):
            return (
                "Great to meet you! Let's discover your entrepreneurial passions. "
                "What industry or area are you most interested in?",
                JourneyStage.IDEA_GENERATION.value,
                '{"user_name": "TestUser", "stage": "idea_generation"}'
            )
        
        mock_onboard.side_effect = mock_run_onboarding
        mock_gen.side_effect = mock_generate_reply
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client_no_mock(override_get_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client without mocking orchestrator.
    
    Use this for tests that need to verify endpoint behavior without AI calls
    but with real database operations.
    """
    app.dependency_overrides[get_session] = override_get_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        {"role": "assistant", "content": "Welcome! What's your name?"},
        {"role": "user", "content": "My name is John"},
        {"role": "assistant", "content": "Nice to meet you, John! What industry interests you?"},
        {"role": "user", "content": "I'm interested in healthcare technology"},
    ]


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_chat_session():
    """Mock ChatSession object."""
    session = MagicMock()
    session.id = "test-session-123"
    session.title = "Test Session"
    session.current_stage = JourneyStage.ONBOARDING.value
    session.stage_context = "{}"
    return session
