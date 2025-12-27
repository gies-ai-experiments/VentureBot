"""Tests for database models.

These tests verify the SQLAlchemy models and their relationships.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.api_gateway.app.database import Base
from services.api_gateway.app.models import (
    ChatSession, ChatMessage, MessageRole, JourneyStage
)


@pytest.fixture
def db_engine():
    """Create in-memory database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(db_engine):
    """Create database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_message_role_values(self):
        """Verify message role enum values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_message_role_is_string_enum(self):
        """Verify MessageRole is a string enum."""
        assert isinstance(MessageRole.USER, str)
        assert MessageRole.USER == "user"


class TestJourneyStage:
    """Tests for JourneyStage enum."""

    def test_journey_stage_values(self):
        """Verify journey stage enum values."""
        assert JourneyStage.ONBOARDING.value == "onboarding"
        assert JourneyStage.IDEA_GENERATION.value == "idea_generation"
        assert JourneyStage.VALIDATION.value == "validation"
        assert JourneyStage.PRD.value == "prd"
        assert JourneyStage.PROMPT_ENGINEERING.value == "prompt_engineering"
        assert JourneyStage.COMPLETE.value == "complete"

    def test_journey_stage_count(self):
        """Verify there are 6 journey stages."""
        stages = list(JourneyStage)
        assert len(stages) == 6


class TestChatSession:
    """Tests for ChatSession model."""

    def test_create_session_with_defaults(self, session):
        """Test creating a session with default values."""
        chat_session = ChatSession(title="Test Session")
        session.add(chat_session)
        session.commit()
        
        assert chat_session.id is not None
        assert chat_session.title == "Test Session"
        assert chat_session.current_stage == JourneyStage.ONBOARDING.value
        assert chat_session.stage_context == "{}"
        assert chat_session.created_at is not None
        assert chat_session.updated_at is not None

    def test_create_session_without_title(self, session):
        """Test creating a session without title."""
        chat_session = ChatSession()
        session.add(chat_session)
        session.commit()
        
        assert chat_session.id is not None
        assert chat_session.title is None

    def test_session_id_is_uuid(self, session):
        """Test that session ID is a valid UUID format."""
        chat_session = ChatSession(title="UUID Test")
        session.add(chat_session)
        session.commit()
        
        # UUID should be 36 characters (8-4-4-4-12 format)
        assert len(chat_session.id) == 36
        assert chat_session.id.count("-") == 4

    def test_session_can_change_stage(self, session):
        """Test changing session stage."""
        chat_session = ChatSession(title="Stage Test")
        session.add(chat_session)
        session.commit()
        
        chat_session.current_stage = JourneyStage.IDEA_GENERATION.value
        session.commit()
        session.refresh(chat_session)
        
        assert chat_session.current_stage == JourneyStage.IDEA_GENERATION.value

    def test_session_can_store_context(self, session):
        """Test storing context JSON."""
        context = '{"user_name": "John", "industry": "Healthcare"}'
        chat_session = ChatSession(title="Context Test", stage_context=context)
        session.add(chat_session)
        session.commit()
        
        session.refresh(chat_session)
        assert chat_session.stage_context == context


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_create_message(self, session):
        """Test creating a chat message."""
        # Create session first
        chat_session = ChatSession(title="Message Test")
        session.add(chat_session)
        session.commit()
        
        # Create message
        message = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.USER.value,
            content="Hello, VentureBot!"
        )
        session.add(message)
        session.commit()
        
        assert message.id is not None
        assert message.session_id == chat_session.id
        assert message.role == MessageRole.USER.value
        assert message.content == "Hello, VentureBot!"
        assert message.created_at is not None

    def test_message_id_is_uuid(self, session):
        """Test that message ID is a valid UUID format."""
        chat_session = ChatSession(title="UUID Test")
        session.add(chat_session)
        session.commit()
        
        message = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.USER.value,
            content="Test"
        )
        session.add(message)
        session.commit()
        
        assert len(message.id) == 36
        assert message.id.count("-") == 4


class TestSessionMessageRelationship:
    """Tests for the relationship between sessions and messages."""

    def test_session_has_messages(self, session):
        """Test that session can access its messages."""
        chat_session = ChatSession(title="Relationship Test")
        session.add(chat_session)
        session.commit()
        
        # Add messages
        msg1 = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.ASSISTANT.value,
            content="Welcome!"
        )
        msg2 = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.USER.value,
            content="Hello!"
        )
        session.add_all([msg1, msg2])
        session.commit()
        
        session.refresh(chat_session)
        assert len(chat_session.messages) == 2

    def test_message_has_session(self, session):
        """Test that message can access its session."""
        chat_session = ChatSession(title="Back-ref Test")
        session.add(chat_session)
        session.commit()
        
        message = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.USER.value,
            content="Test"
        )
        session.add(message)
        session.commit()
        
        session.refresh(message)
        assert message.session.title == "Back-ref Test"

    def test_cascade_delete(self, session):
        """Test that deleting session deletes messages."""
        chat_session = ChatSession(title="Cascade Test")
        session.add(chat_session)
        session.commit()
        session_id = chat_session.id
        
        # Add message
        message = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER.value,
            content="Test"
        )
        session.add(message)
        session.commit()
        message_id = message.id
        
        # Delete session
        session.delete(chat_session)
        session.commit()
        
        # Verify message is also deleted
        deleted_message = session.get(ChatMessage, message_id)
        assert deleted_message is None
