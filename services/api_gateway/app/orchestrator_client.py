from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Tuple

from services.orchestrator.chat_orchestrator import ChatOrchestrator
from services.orchestrator.flows.staged_journey_flow import JourneyStage

LOGGER = logging.getLogger(__name__)

orchestrator = ChatOrchestrator()


async def generate_assistant_reply(
    session_id: str,
    conversation: List[Dict[str, str]],
    current_stage: str = JourneyStage.ONBOARDING,
    stored_context_json: str = "{}",
) -> Tuple[str, str, str]:
    """
    Invoke the CrewAI orchestrator in a worker thread to avoid blocking.
    
    Args:
        session_id: The session identifier
        conversation: List of conversation messages
        current_stage: The current stage in the journey
        stored_context_json: JSON string of accumulated stage context
        
    Returns:
        Tuple of (reply_text, next_stage, updated_context_json)
    """
    LOGGER.info("Generating assistant reply for session %s, stage: %s", session_id, current_stage)

    def _run() -> Tuple[str, str, str]:
        try:
            result = orchestrator.generate_response(
                session_id=session_id,
                messages=conversation,
                current_stage=current_stage,
                stored_context_json=stored_context_json,
            )
            LOGGER.info("Assistant reply generated for session %s, next stage: %s", session_id, result[1])
            return result
        except Exception as exc:
            LOGGER.error(
                "Orchestrator execution failed for session %s: %s",
                session_id,
                exc,
                exc_info=True,
            )
            return (
                "I apologize, but I encountered an error processing your request. "
                "Please try again or rephrase your message.",
                current_stage,
                stored_context_json,
            )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run)


async def run_onboarding(
    session_id: str,
    stored_context_json: str = "{}",
) -> Tuple[str, str, str]:
    """
    Run the onboarding stage automatically for a new session.
    
    This is called when a session is first created to kick off the
    onboarding agent without waiting for user input.
    
    Args:
        session_id: The session identifier
        stored_context_json: JSON string of initial context (usually empty)
        
    Returns:
        Tuple of (onboarding_output, next_stage, updated_context_json)
    """
    LOGGER.info("Running auto-onboarding for session %s", session_id)

    def _run() -> Tuple[str, str, str]:
        try:
            result = orchestrator.run_onboarding(
                session_id=session_id,
                stored_context_json=stored_context_json,
            )
        except Exception as exc:
            LOGGER.error(
                "Onboarding execution failed for session %s: %s",
                session_id,
                exc,
                exc_info=True,
            )
            return (
                "👋 Welcome to VentureBot! I'm here to help you discover and build "
                "your next great startup idea.\n\n"
                "I apologize, but I encountered an issue starting our conversation. "
                "Please send me a message to begin - tell me about yourself, your interests, "
                "and any frustrations or pain points you've experienced that could inspire "
                "a business idea.",
                JourneyStage.ONBOARDING,
                stored_context_json,
            )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run)

