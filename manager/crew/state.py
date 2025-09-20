"""Session state management for VentureBot Crew workflow."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class Stage(str, Enum):
    """Workflow stages for the VentureBot multi-agent system."""

    ONBOARDING = "onboarding"
    IDEA_GENERATION = "idea_generation"
    IDEA_SELECTION = "idea_selection"
    VALIDATION = "validation"
    PRODUCT_STRATEGY = "product_strategy"
    PRODUCT_REFINEMENT = "product_refinement"
    PROMPT_ENGINEERING = "prompt_engineering"
    COMPLETE = "complete"


@dataclass
class SessionState:
    """In-memory representation of a user session."""

    session_id: str
    user_id: str
    stage: Stage = Stage.ONBOARDING
    memory: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def append_history(self, role: str, content: str) -> None:
        """Append a message to the conversation history and update timestamps."""
        self.history.append({"role": role, "content": content})
        self.updated_at = datetime.now(timezone.utc)


__all__ = ["Stage", "SessionState"]
