from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .flows.staged_journey_flow import (
    JourneyStage,
    StageContext,
    StageResult,
    get_executor,
)

LOGGER = logging.getLogger(__name__)


class ChatOrchestrator:
    """
    Stage-aware orchestrator for VentureBots entrepreneurship journey.
    
    This orchestrator runs one stage at a time, waiting for user input
    between each stage to create a human-in-the-loop experience.
    """

    def __init__(self) -> None:
        self._executor = get_executor()

    def _format_conversation(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format conversation messages for context."""
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "").strip()}
            for msg in messages
        ]

    def _infer_user_name(self, messages: List[Dict[str, str]]) -> str:
        """Infer user name from conversation."""
        user_pattern = re.compile(
            r"(?:my name is|i'm|i am)\s+([A-Za-z][A-Za-z\s'-]{1,40})", re.IGNORECASE
        )
        for message in messages:
            if message.get("role") != "user":
                continue
            match = user_pattern.search(message.get("content", ""))
            if match:
                name_candidate = match.group(1).strip().split()[0]
                return name_candidate.capitalize()
        return "Founder"

    def _infer_industry_focus(self, messages: List[Dict[str, str]]) -> str:
        """Infer industry focus from conversation."""
        for message in reversed(messages):
            if message.get("role") != "user":
                continue
            text = message.get("content", "")
            industry_match = re.search(
                r"industry[:\s]+([A-Za-z\s&/-]{3,60})", text, re.IGNORECASE
            )
            if industry_match:
                return industry_match.group(1).strip().title()
        return "General entrepreneurship"

    def _infer_startup_idea(self, messages: List[Dict[str, str]], stage_context: StageContext) -> str:
        """
        Infer the startup idea from conversation.
        
        For idea generation stage, use the user's selected idea number.
        For validation and later stages, use stored context.
        """
        # If we already have a startup idea from context, use it
        if stage_context.startup_idea:
            return stage_context.startup_idea
        
        # Check if user selected an idea by number
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "").strip()
                # Check for idea selection (e.g., "1", "idea 2", "I like option 3")
                number_match = re.search(r'\b([1-7])\b', content)
                if number_match and stage_context.idea_slate:
                    # User selected an idea number - extract that idea from the slate
                    return f"User selected idea #{number_match.group(1)} from the generated ideas"
                if content:
                    return content
        
        return "Exploring new venture ideas"

    def _build_stage_context(
        self,
        messages: List[Dict[str, str]],
        stored_context_json: str = "{}",
    ) -> StageContext:
        """Build stage context from messages and stored context."""
        # Start with stored context from previous stages
        context = StageContext.from_json(stored_context_json)
        
        # Update with inferred values from conversation
        context.user_name = self._infer_user_name(messages)
        context.industry_focus = self._infer_industry_focus(messages)
        context.conversation_history = self._format_conversation(messages)
        
        # Get the latest user message
        for message in reversed(messages):
            if message.get("role") == "user":
                context.user_message = message.get("content", "").strip()
                break
        
        # Infer startup idea based on context
        context.startup_idea = self._infer_startup_idea(messages, context)
        
        return context

    def run_onboarding(
        self,
        session_id: str,
        stored_context_json: str = "{}",
    ) -> Tuple[str, str, str]:
        """
        Run the onboarding stage automatically for a new session.
        
        Returns:
            Tuple of (output_text, next_stage, updated_context_json)
        """
        context = StageContext.from_json(stored_context_json)
        
        LOGGER.info(f"Running auto-onboarding for session {session_id}")
        
        result = self._executor.run_onboarding_auto(context)
        
        return (
            result.output,
            result.next_stage,
            result.context.to_json(),
        )

    def run_next_stage(
        self,
        session_id: str,
        current_stage: str,
        messages: List[Dict[str, str]],
        stored_context_json: str = "{}",
    ) -> Tuple[str, str, str]:
        """
        Run the next stage in the journey based on current stage.
        
        This is called when the user responds after a stage output.
        
        Args:
            session_id: The session identifier
            current_stage: The stage that was just completed
            messages: Full conversation history
            stored_context_json: JSON string of stored stage context
            
        Returns:
            Tuple of (output_text, next_stage, updated_context_json)
        """
        # Build context from conversation and stored state
        context = self._build_stage_context(messages, stored_context_json)
        
        # The current_stage passed in is already the next stage to run
        # (updated by the previous stage execution).
        next_stage = current_stage
        
        LOGGER.info(
            f"Session {session_id}: Moving from {current_stage} to {next_stage}"
        )
        
        # If journey is complete, return completion message
        if next_stage == JourneyStage.COMPLETE:
            return (
                "🎉 **Congratulations!** You've completed the full VentureBot entrepreneurship journey!\n\n"
                "Here's what we've accomplished together:\n"
                "1. ✅ Discovered your pain points and motivations\n"
                "2. ✅ Generated innovative startup ideas\n"
                "3. ✅ Validated your chosen idea in the market\n"
                "4. ✅ Created a comprehensive Product Requirements Document\n"
                "5. ✅ Generated no-code builder prompts for implementation\n\n"
                "Would you like to:\n"
                "- **Start a new venture exploration** - Begin a fresh journey\n"
                "- **Revisit any previous step** - Let me know which stage to refine",
                JourneyStage.COMPLETE,
                context.to_json(),
            )
        
        # Run the next stage
        result = self._executor.run_stage(next_stage, context)
        
        return (
            result.output,
            result.next_stage,
            result.context.to_json(),
        )

    def generate_response(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        current_stage: str = JourneyStage.ONBOARDING,
        stored_context_json: str = "{}",
    ) -> Tuple[str, str, str]:
        """
        Generate a response for the current conversation state.
        
        This is the main entry point for processing user messages.
        
        Args:
            session_id: The session identifier
            messages: Full conversation history
            current_stage: The current stage in the journey
            stored_context_json: JSON string of stored stage context
            
        Returns:
            Tuple of (output_text, next_stage, updated_context_json)
        """
        LOGGER.info(f"Generating response for session {session_id} in stage {current_stage}")
        user_message = messages[-1]["content"].strip() if messages else ""
        
        if not user_message:
            return (
                "I'm here whenever you want to explore your venture ideas.",
                current_stage,
                stored_context_json,
            )
        
        try:
            return self.run_next_stage(
                session_id=session_id,
                current_stage=current_stage,
                messages=messages,
                stored_context_json=stored_context_json,
            )
        except Exception as exc:
            LOGGER.exception(
                f"Stage execution failed for session {session_id}: {exc}"
            )
            return (
                "I apologize, but I encountered an error processing your request. "
                "Please try again or rephrase your message.",
                current_stage,
                stored_context_json,
            )
