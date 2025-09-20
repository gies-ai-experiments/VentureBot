"""Helper utilities for CrewAI based VentureBot workflow."""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


def summarise_history(history: Iterable[Dict[str, str]], limit: int = 6) -> str:
    """Render the tail of the conversation history as a compact string."""
    if not history:
        return ""
    recent = list(history)[-limit:]
    return "\n".join(f"{item['role'].upper()}: {item['content']}" for item in recent)


def merge_memory(existing: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge nested memory dictionaries, overwriting scalar leaves."""
    if not updates:
        return existing

    for key, value in updates.items():
        if isinstance(value, dict):
            existing_value = existing.get(key, {})
            if not isinstance(existing_value, dict):
                existing_value = {}
            existing[key] = merge_memory(existing_value, value)
        else:
            existing[key] = value
    return existing


def normalise_text(value: str) -> str:
    """Normalise whitespace for logging or display purposes."""
    return " ".join(value.split())


def dump_json(data: Any) -> str:
    """Serialise dictionaries/lists to a deterministic JSON string for prompts."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)


__all__ = ["summarise_history", "merge_memory", "normalise_text", "dump_json"]
