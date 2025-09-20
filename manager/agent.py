"""Compatibility module exposing a ready-to-use VentureBot service instance."""
from __future__ import annotations

from manager.service import VentureBotService

# Singleton-style service used by FastAPI entrypoints and tests
venturebot_service = VentureBotService()

__all__ = ["venturebot_service", "VentureBotService"]
