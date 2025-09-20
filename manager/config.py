"""Configuration helpers for VentureBot multi-agent crew."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class VentureConfig:
    """Runtime configuration values sourced from YAML + environment defaults."""

    model: str = "gemini/gemini-1.5-flash"
    num_ideas: int = 5
    validation_threshold: float = 0.7
    temperature: float = 0.4
    max_tokens: int = 4096
    verbose_agents: bool = False

    @classmethod
    def from_yaml(cls, path: Path) -> "VentureConfig":
        data: Dict[str, Any] = {}
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
                if not isinstance(loaded, dict):
                    raise ValueError("manager/config.yaml must contain a mapping")
                data = loaded
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


def load_config() -> VentureConfig:
    """Load the VentureBot configuration from manager/config.yaml."""

    project_root = Path(__file__).resolve().parent
    config_path = project_root / "config.yaml"
    return VentureConfig.from_yaml(config_path)


__all__ = ["VentureConfig", "load_config"]
