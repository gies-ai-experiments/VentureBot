"""Pydantic models describing structured outputs returned by CrewAI tasks."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OnboardingResponse(BaseModel):
    """Structured response for the onboarding agent."""

    message: str = Field(..., description="Markdown-formatted message to present to the user.")
    memory_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Nested dictionary containing any memory keys that should be updated.",
    )
    pending_fields: List[str] = Field(
        default_factory=list,
        description="List of memory fields that still require user input (e.g. USER_PROFILE.name).",
    )
    ready_for_ideas: bool = Field(
        False,
        description="Whether the onboarding information is complete and the flow can progress to idea generation.",
    )


class IdeaSummary(BaseModel):
    """Representation of a single startup idea."""

    id: int = Field(..., description="Identifier for the idea, starting at 1.")
    idea: str = Field(..., description="Short statement describing the idea in <= 15 words.")
    concept: str = Field(
        ..., description="BADM 350 concept(s) leveraged by the idea, e.g. Network Effects."
    )


class IdeaGenerationResponse(BaseModel):
    """Structured output for idea generation."""

    message: str = Field(..., description="User-facing markdown content listing the ideas.")
    ideas: List[IdeaSummary] = Field(..., description="Ideas to store in memory.")


class ValidationScore(BaseModel):
    """Score components returned by the validator agent."""

    feasibility: float = Field(..., ge=0.0, le=1.0, description="Execution feasibility score.")
    innovation: float = Field(..., ge=0.0, le=1.0, description="Innovation potential score.")
    overall: float = Field(..., ge=0.0, le=1.0, description="Weighted overall score.")
    notes: str = Field(..., description="Short narrative explaining the evaluation.")


class ValidationResponse(BaseModel):
    """Structured response for validation outcomes."""

    message: str = Field(..., description="Markdown formatted summary to show the user.")
    score: ValidationScore = Field(..., description="Quantitative assessment of the idea.")


class ProductRequirements(BaseModel):
    """Structured PRD information retained in memory."""

    overview: str = Field(..., description="One sentence overview and value proposition.")
    target_users: List[str] = Field(
        ..., description="List of personas with needs, each entry as a brief sentence."
    )
    user_stories: List[str] = Field(..., description="List of user stories in 'As a... I want... so that...' format.")
    functional_requirements: List[str] = Field(..., description="Functional requirement bullets.")
    nonfunctional_requirements: List[str] = Field(
        ..., description="Non-functional requirement bullets (e.g. usability, performance)."
    )
    success_metrics: List[str] = Field(..., description="Key KPIs to track success.")


class ProductPlanResponse(BaseModel):
    """Response from the product manager agent."""

    message: str = Field(..., description="PRD rendered for the user in markdown.")
    prd: ProductRequirements = Field(..., description="Structured PRD to save in memory.")
    ready_for_prompt: bool = Field(
        False,
        description="Whether the flow should advance automatically to prompt engineering.",
    )


class PromptResponse(BaseModel):
    """Prompt engineer output."""

    message: str = Field(..., description="Readable prompt delivered to the user.")
    builder_prompt: str = Field(..., description="Raw prompt to store in memory for no-code builders.")
    follow_up: Optional[str] = Field(
        None,
        description="Optional follow-up question or call-to-action to keep the conversation going.",
    )


__all__ = [
    "OnboardingResponse",
    "IdeaGenerationResponse",
    "IdeaSummary",
    "ValidationResponse",
    "ValidationScore",
    "ProductPlanResponse",
    "ProductRequirements",
    "PromptResponse",
]
