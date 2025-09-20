"""High-level service interface used by the FastAPI and Chainlit adapters."""
from __future__ import annotations

from typing import Dict, Optional

from manager.config import VentureConfig, load_config
from manager.crew.state import Stage
from manager.crew.workflow import VentureBotCrew


class VentureBotService:
    """Facade over the VentureBotCrew that exposes session-oriented helpers."""

    def __init__(self, config: Optional[VentureConfig] = None) -> None:
        self.config = config or load_config()
        self.crew = VentureBotCrew(self.config)

    def create_session(self, user_id: str) -> Dict[str, str]:
        state = self.crew.create_session(user_id)
        initial_message = state.history[-1]["content"] if state.history else "Hello!"
        return {
            "session_id": state.session_id,
            "initial_message": initial_message,
            "stage": state.stage.value,
        }

    def chat(self, session_id: str, message: str) -> Dict[str, object]:
        reply = self.crew.handle_message(session_id, message)
        state = self.crew.get_session(session_id)
        return {
            "message": reply,
            "stage": state.stage.value,
            "memory": state.memory,
        }

    def snapshot(self, session_id: str) -> Dict[str, object]:
        return self.crew.snapshot(session_id)

    def reset(self, session_id: str) -> Dict[str, str]:
        state = self.crew.create_session(self.crew.get_session(session_id).user_id)
        return {
            "session_id": state.session_id,
            "initial_message": state.history[-1]["content"] if state.history else "Hello again!",
            "stage": state.stage.value,
        }


__all__ = ["VentureBotService"]
