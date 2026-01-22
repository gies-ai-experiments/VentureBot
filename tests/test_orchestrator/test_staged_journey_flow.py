"""Tests for staged_journey_flow intent detection and stage transitions."""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from services.orchestrator.flows.staged_journey_flow import (
    StagedJourneyExecutor,
    StageContext,
    JourneyStage,
)


class TestIntentDetection:
    """Tests for _detect_stage_transition_intent method."""

    @pytest.fixture
    def executor(self):
        """Create executor with mocked blueprint to avoid CrewAI initialization."""
        with patch(
            "services.orchestrator.flows.staged_journey_flow.VenturebotsAiEntrepreneurshipCoachingPlatformCrew"
        ):
            return StagedJourneyExecutor()

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            {"role": "assistant", "content": "Welcome! What's your name?"},
            {"role": "user", "content": "I'm John"},
            {"role": "assistant", "content": "Nice to meet you! What industry interests you?"},
            {"role": "user", "content": "I'm interested in healthcare technology"},
        ]

    def test_detect_intent_should_proceed_high_confidence(
        self, executor, sample_conversation_history
    ):
        """Test that explicit readiness messages trigger proceed with high confidence."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"should_proceed": true, "confidence": 0.9, "reason": "User explicitly ready"}'
                )
            )
        ]

        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            result = executor._detect_stage_transition_intent(
                user_message="I'm ready to see some ideas now",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=sample_conversation_history,
            )

            assert result["should_proceed"] is True
            assert result["confidence"] >= 0.7
            mock_client.chat.completions.create.assert_called_once()

    def test_detect_intent_should_not_proceed(
        self, executor, sample_conversation_history
    ):
        """Test that follow-up questions don't trigger proceed."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"should_proceed": false, "confidence": 0.85, "reason": "User asking follow-up question"}'
                )
            )
        ]

        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            result = executor._detect_stage_transition_intent(
                user_message="Can you tell me more about what kind of ideas you can help with?",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=sample_conversation_history,
            )

            assert result["should_proceed"] is False

    def test_detect_intent_low_confidence_does_not_proceed(
        self, executor, sample_conversation_history
    ):
        """Test that low confidence results don't trigger transition."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"should_proceed": true, "confidence": 0.5, "reason": "Ambiguous message"}'
                )
            )
        ]

        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            result = executor._detect_stage_transition_intent(
                user_message="maybe I could look at some options",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=sample_conversation_history,
            )

            # Even if should_proceed is True, confidence is below 0.7 threshold
            assert result["confidence"] < 0.7

    def test_detect_intent_handles_api_error(
        self, executor, sample_conversation_history
    ):
        """Test graceful handling of API errors."""
        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            result = executor._detect_stage_transition_intent(
                user_message="show me ideas",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=sample_conversation_history,
            )

            # Should return safe default (no transition) on error
            assert result["should_proceed"] is False
            assert result["confidence"] == 0.0
            assert "Detection failed" in result["reason"]

    def test_detect_intent_handles_json_in_code_block(
        self, executor, sample_conversation_history
    ):
        """Test handling of JSON wrapped in markdown code blocks."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='```json\n{"should_proceed": true, "confidence": 0.95, "reason": "Clear intent"}\n```'
                )
            )
        ]

        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            result = executor._detect_stage_transition_intent(
                user_message="I'm ready, let's see the ideas",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=sample_conversation_history,
            )

            assert result["should_proceed"] is True
            assert result["confidence"] == 0.95

    def test_detect_intent_with_empty_history(self, executor):
        """Test intent detection with empty conversation history."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"should_proceed": false, "confidence": 0.8, "reason": "No context yet"}'
                )
            )
        ]

        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            result = executor._detect_stage_transition_intent(
                user_message="Hello",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=[],
            )

            assert result["should_proceed"] is False


class TestStageTransition:
    """Tests for run_stage with immediate transition behavior."""

    @pytest.fixture
    def executor(self):
        """Create executor with mocked blueprint."""
        with patch(
            "services.orchestrator.flows.staged_journey_flow.VenturebotsAiEntrepreneurshipCoachingPlatformCrew"
        ):
            return StagedJourneyExecutor()

    @pytest.fixture
    def context_with_history(self):
        """Create a context with sufficient conversation history."""
        context = StageContext(
            user_name="TestUser",
            industry_focus="Healthcare",
            user_message="I'm ready for ideas",
            conversation_history=[
                {"role": "assistant", "content": "Welcome!"},
                {"role": "user", "content": "Hi, I'm John"},
                {"role": "assistant", "content": "What interests you?"},
                {"role": "user", "content": "Healthcare tech"},
            ],
            onboarding_summary="User John interested in healthcare technology",
        )
        return context

    def test_minimum_context_required(self, executor):
        """Test that transition doesn't happen without minimum context."""
        context = StageContext(
            user_name="TestUser",
            user_message="I'm ready for ideas",
            conversation_history=[
                {"role": "user", "content": "Hi"},
            ],  # Only 1 exchange
            onboarding_summary=None,  # No onboarding summary yet - key for minimum context check
        )

        # Mock intent detection to return no-proceed (simulating insufficient context)
        mock_intent = {
            "should_proceed": False,
            "confidence": 0.3,
            "reason": "Not enough context shared yet",
        }

        with patch.object(executor, "_run_onboarding_direct", return_value="Onboarding response"), \
             patch.object(executor, "_detect_stage_transition_intent", return_value=mock_intent):
            result = executor.run_stage(JourneyStage.ONBOARDING, context)

        # Should stay in onboarding due to low-confidence intent detection
        assert result.next_stage == JourneyStage.ONBOARDING

    def test_transition_with_high_confidence_intent(self, executor, context_with_history):
        """Test that high confidence intent triggers transition to next stage."""
        mock_intent = {
            "should_proceed": True,
            "confidence": 0.9,
            "reason": "User ready",
        }

        with patch.object(executor, "_run_onboarding_direct", return_value="Onboarding complete"), \
             patch.object(executor, "_detect_stage_transition_intent", return_value=mock_intent):

            result = executor.run_stage(JourneyStage.ONBOARDING, context_with_history)

        # result.stage is the stage that ran (onboarding)
        assert result.stage == JourneyStage.ONBOARDING
        # result.next_stage should be idea_generation after successful transition
        assert result.next_stage == JourneyStage.IDEA_GENERATION

    def test_no_transition_with_low_confidence(self, executor, context_with_history):
        """Test that low confidence doesn't trigger transition."""
        mock_intent = {
            "should_proceed": True,
            "confidence": 0.4,  # Below 0.5 threshold
            "reason": "Ambiguous",
        }

        with patch.object(executor, "_run_task", return_value="Onboarding response"), \
             patch.object(executor, "_detect_stage_transition_intent", return_value=mock_intent):

            result = executor.run_stage(JourneyStage.ONBOARDING, context_with_history)

        # Should stay in onboarding
        assert result.next_stage == JourneyStage.ONBOARDING

    def test_non_onboarding_stage_with_confirmation(self, executor):
        """Test that validation stage requires user confirmation to advance."""
        context = StageContext(
            user_name="TestUser",
            user_message="This looks good, let's continue",
            onboarding_summary="User onboarded",
            idea_slate="Generated ideas",
        )

        mock_intent = {
            "should_proceed": True,
            "confidence": 0.8,
            "reason": "User confirmed",
        }

        with patch.object(executor, "_run_task", return_value="Validation complete"), \
             patch.object(executor, "_detect_stage_transition_intent", return_value=mock_intent):
            result = executor.run_stage(JourneyStage.VALIDATION, context)

        # With confirmation, should advance to PRD
        assert result.next_stage == JourneyStage.PRD


class TestIntentDetectionPrompt:
    """Tests to verify the prompt construction for intent detection."""

    @pytest.fixture
    def executor(self):
        """Create executor with mocked blueprint."""
        with patch(
            "services.orchestrator.flows.staged_journey_flow.VenturebotsAiEntrepreneurshipCoachingPlatformCrew"
        ):
            return StagedJourneyExecutor()

    def test_prompt_includes_conversation_context(self, executor):
        """Verify that the prompt sent to LLM includes conversation history."""
        conversation_history = [
            {"role": "assistant", "content": "Welcome to VentureBot!"},
            {"role": "user", "content": "I want to build a health app"},
        ]

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"should_proceed": false, "confidence": 0.8, "reason": "test"}'
                )
            )
        ]

        with patch("services.orchestrator.flows.staged_journey_flow.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            executor._detect_stage_transition_intent(
                user_message="Let's proceed",
                current_stage=JourneyStage.ONBOARDING,
                conversation_history=conversation_history,
            )

            # Verify the prompt was constructed and sent
            call_args = mock_client.chat.completions.create.call_args
            prompt_content = call_args.kwargs["messages"][0]["content"]

            # Check that key elements are in the prompt
            assert "Onboarding" in prompt_content
            assert "Idea Generation" in prompt_content
            assert "Let's proceed" in prompt_content
            assert "health app" in prompt_content  # From conversation history
