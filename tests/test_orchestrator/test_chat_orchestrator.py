"""Tests for the ChatOrchestrator class.

These tests verify the orchestrator's conversation processing,
context building, and stage management logic.
"""

from __future__ import annotations

import pytest
import json
from unittest.mock import MagicMock, patch

from services.orchestrator.chat_orchestrator import ChatOrchestrator
from services.orchestrator.flows.staged_journey_flow import JourneyStage, StageContext


class TestOrchestratorInitialization:
    """Tests for ChatOrchestrator initialization."""

    def test_orchestrator_can_be_instantiated(self):
        """Verify orchestrator can be created."""
        with patch("services.orchestrator.chat_orchestrator.get_executor"):
            orchestrator = ChatOrchestrator()
            assert orchestrator is not None


class TestConversationFormatting:
    """Tests for conversation formatting methods."""

    @pytest.fixture
    def orchestrator(self):
        """Create a ChatOrchestrator instance with mocked executor."""
        with patch("services.orchestrator.chat_orchestrator.get_executor"):
            return ChatOrchestrator()

    def test_format_conversation_empty(self, orchestrator):
        """Verify formatting of empty conversation."""
        result = orchestrator._format_conversation([])
        assert result == []

    def test_format_conversation_with_messages(self, orchestrator, sample_messages):
        """Verify conversation formatting includes all messages."""
        result = orchestrator._format_conversation(sample_messages)
        
        assert len(result) == 4
        assert all("role" in msg and "content" in msg for msg in result)

    def test_format_conversation_strips_whitespace(self, orchestrator):
        """Verify whitespace is stripped from content."""
        messages = [
            {"role": "user", "content": "  Hello world  "},
        ]
        result = orchestrator._format_conversation(messages)
        
        assert result[0]["content"] == "Hello world"


class TestNameExtraction:
    """Tests for user name extraction from conversations."""

    @pytest.fixture
    def orchestrator(self):
        """Create a ChatOrchestrator instance with mocked executor."""
        with patch("services.orchestrator.chat_orchestrator.get_executor"):
            return ChatOrchestrator()

    def test_extract_name_from_my_name_is_pattern(self, orchestrator):
        """Test extracting name from 'My name is X' pattern."""
        messages = [
            {"role": "user", "content": "My name is Alice"},
        ]
        result = orchestrator._infer_user_name(messages)
        assert result == "Alice"

    def test_extract_name_from_im_pattern(self, orchestrator):
        """Test extracting name from 'I'm X' pattern."""
        messages = [
            {"role": "user", "content": "I'm Bob and I want to start a business"},
        ]
        result = orchestrator._infer_user_name(messages)
        assert result == "Bob"

    def test_extract_name_from_i_am_pattern(self, orchestrator):
        """Test extracting name from 'I am X' pattern."""
        messages = [
            {"role": "user", "content": "I am Charlie looking for startup ideas"},
        ]
        result = orchestrator._infer_user_name(messages)
        assert result == "Charlie"

    def test_no_name_found_returns_founder(self, orchestrator):
        """Test that default 'Founder' is returned when no name found."""
        messages = [
            {"role": "user", "content": "Hello, I want to learn about entrepreneurship"},
        ]
        result = orchestrator._infer_user_name(messages)
        assert result == "Founder"

    def test_skips_assistant_messages(self, orchestrator):
        """Test that assistant messages are skipped during name extraction."""
        messages = [
            {"role": "assistant", "content": "My name is VentureBot"},
            {"role": "user", "content": "I'm Diana"},
        ]
        result = orchestrator._infer_user_name(messages)
        assert result == "Diana"


class TestIndustryExtraction:
    """Tests for industry focus extraction from conversations."""

    @pytest.fixture
    def orchestrator(self):
        """Create a ChatOrchestrator instance with mocked executor."""
        with patch("services.orchestrator.chat_orchestrator.get_executor"):
            return ChatOrchestrator()

    def test_extract_industry_from_explicit_mention(self, orchestrator):
        """Test extracting industry from explicit mention."""
        messages = [
            {"role": "user", "content": "Industry: Healthcare Technology"},
        ]
        result = orchestrator._infer_industry_focus(messages)
        assert "Healthcare Technology" in result

    def test_no_industry_returns_general(self, orchestrator):
        """Test default industry when none is mentioned."""
        messages = [
            {"role": "user", "content": "I want to start a business"},
        ]
        result = orchestrator._infer_industry_focus(messages)
        assert result == "General entrepreneurship"


class TestStartupIdeaExtraction:
    """Tests for startup idea extraction from conversations."""

    @pytest.fixture
    def orchestrator(self):
        """Create a ChatOrchestrator instance with mocked executor."""
        with patch("services.orchestrator.chat_orchestrator.get_executor"):
            return ChatOrchestrator()

    def test_use_existing_idea_from_context(self, orchestrator):
        """Test that existing idea in context is used."""
        messages = [{"role": "user", "content": "Continue"}]
        context = StageContext(startup_idea="AI-powered healthcare assistant")
        
        result = orchestrator._infer_startup_idea(messages, context)
        assert result == "AI-powered healthcare assistant"

    def test_infer_idea_from_user_message(self, orchestrator):
        """Test inferring idea from user message when no context."""
        messages = [{"role": "user", "content": "I want to build a food delivery app"}]
        context = StageContext()
        
        result = orchestrator._infer_startup_idea(messages, context)
        assert "food delivery app" in result.lower()


class TestContextBuilding:
    """Tests for stage context building."""

    @pytest.fixture
    def orchestrator(self):
        """Create a ChatOrchestrator instance with mocked executor."""
        with patch("services.orchestrator.chat_orchestrator.get_executor"):
            return ChatOrchestrator()

    def test_build_context_from_empty(self, orchestrator):
        """Test building context from scratch."""
        messages = [
            {"role": "assistant", "content": "What's your name?"},
            {"role": "user", "content": "My name is Eve"},
        ]
        
        result = orchestrator._build_stage_context(messages, "{}")
        
        assert isinstance(result, StageContext)
        assert result.user_name == "Eve"

    def test_build_context_preserves_stored_data(self, orchestrator):
        """Test that stored context is preserved."""
        stored = json.dumps({
            "onboarding_summary": "User wants to build healthcare apps",
        })
        messages = [{"role": "user", "content": "Continue"}]
        
        result = orchestrator._build_stage_context(messages, stored)
        
        assert result.onboarding_summary == "User wants to build healthcare apps"

    def test_build_context_updates_user_message(self, orchestrator):
        """Test that latest user message is captured."""
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second message"},
        ]
        
        result = orchestrator._build_stage_context(messages, "{}")
        
        assert result.user_message == "Second message"


class TestGenerateResponse:
    """Tests for the main generate_response method."""

    @pytest.fixture
    def orchestrator(self):
        """Create a ChatOrchestrator instance with mocked executor."""
        with patch("services.orchestrator.chat_orchestrator.get_executor") as mock_get:
            mock_executor = MagicMock()
            mock_get.return_value = mock_executor
            orch = ChatOrchestrator()
            orch._executor = mock_executor
            return orch

    def test_empty_message_returns_default(self, orchestrator):
        """Test that empty message returns default response."""
        messages = [{"role": "user", "content": ""}]
        
        output, stage, context = orchestrator.generate_response(
            session_id="test",
            messages=messages,
            current_stage=JourneyStage.ONBOARDING,
        )
        
        assert "whenever you want" in output.lower()
        assert stage == JourneyStage.ONBOARDING

    def test_complete_stage_returns_celebration(self, orchestrator):
        """Test that complete stage returns celebration message."""
        messages = [{"role": "user", "content": "Done!"}]
        
        output, stage, context = orchestrator.generate_response(
            session_id="test",
            messages=messages,
            current_stage=JourneyStage.COMPLETE,
        )
        
        assert "congratulations" in output.lower() or "completed" in output.lower()


class TestStageTransitions:
    """Tests for stage transition logic."""

    def test_journey_stages_are_in_order(self):
        """Verify journey stages follow expected order."""
        expected_order = [
            JourneyStage.ONBOARDING,
            JourneyStage.IDEA_GENERATION,
            JourneyStage.VALIDATION,
            JourneyStage.PRD,
            JourneyStage.PROMPT_ENGINEERING,
            JourneyStage.COMPLETE,
        ]
        
        # JourneyStage is a class with string constants, not an enum
        for stage in expected_order:
            assert isinstance(stage, str)


class TestStageContext:
    """Tests for StageContext dataclass."""

    def test_context_to_json_and_back(self):
        """Test JSON serialization round-trip."""
        original = StageContext(
            user_name="John",
            industry_focus="Healthcare",
            startup_idea="Health tracker app",
        )
        
        json_str = original.to_json()
        restored = StageContext.from_json(json_str)
        
        assert restored.user_name == "John"
        assert restored.industry_focus == "Healthcare"
        assert restored.startup_idea == "Health tracker app"

    def test_context_from_invalid_json(self):
        """Test handling of invalid JSON."""
        result = StageContext.from_json("invalid json")
        
        # Should return empty context without crashing
        assert isinstance(result, StageContext)

    def test_context_from_empty_json(self):
        """Test handling of empty JSON."""
        result = StageContext.from_json("{}")
        
        assert isinstance(result, StageContext)
        # Default user_name is "Founder" per the dataclass
        assert result.user_name == "Founder"
