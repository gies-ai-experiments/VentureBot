#!/usr/bin/env python3
"""Quick diagnostic tests for the CrewAI powered VentureBot stack."""
from __future__ import annotations

import os
import sys
from typing import Dict

import pytest

# Ensure project root on path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from manager.config import VentureConfig  # noqa: E402
from manager.crew import schemas as crew_schemas  # noqa: E402
from manager.service import VentureBotService  # noqa: E402


def _stub_agents(_: VentureConfig) -> Dict[str, object]:
    """Return lightweight placeholders for agent registry during tests."""
    return {
        "onboarding": object(),
        "idea": object(),
        "validator": object(),
        "product_manager": object(),
        "prompt_engineer": object(),
    }


@pytest.fixture(autouse=True)
def patch_agents(monkeypatch):
    monkeypatch.setattr("manager.crew.workflow.build_agents", _stub_agents)


@pytest.fixture(autouse=True)
def patch_execute_task(monkeypatch):
    def _fake_execute(self, agent_key, description, expected_output, output_model, inputs=None):
        if output_model is crew_schemas.OnboardingResponse:
            return crew_schemas.OnboardingResponse(
                message="👋 Welcome to VentureBot! Let's build something great.",
                memory_updates={
                    "USER_PROFILE": {"name": "Alex"},
                    "USER_PAIN": {"description": "Waiting in long queues", "category": "functional"},
                    "USER_PREFERENCES": {"interests": "Productivity", "activities": "Reading"},
                },
                pending_fields=[],
                ready_for_ideas=True,
            )
        if output_model is crew_schemas.IdeaGenerationResponse:
            ideas = [
                crew_schemas.IdeaSummary(id=1, idea="Mobile queue skipper", concept="IT as Competitive Advantage"),
                crew_schemas.IdeaSummary(id=2, idea="Predictive wait-time board", concept="Data-driven value"),
            ]
            return crew_schemas.IdeaGenerationResponse(
                message="Here are two concepts to explore...", ideas=ideas
            )
        if output_model is crew_schemas.ValidationResponse:
            return crew_schemas.ValidationResponse(
                message="Validation complete – the concept looks promising!",
                score=crew_schemas.ValidationScore(
                    feasibility=0.72, innovation=0.58, overall=0.66, notes="Crowdsourced data reduces friction."
                ),
            )
        if output_model is crew_schemas.ProductPlanResponse:
            return crew_schemas.ProductPlanResponse(
                message="Draft PRD ready. **Ready to build your product with no-code tools, or refine further?**",
                prd=crew_schemas.ProductRequirements(
                    overview="App provides instant queue insights for busy professionals.",
                    target_users=["Young commuters seeking time savings", "Parents balancing chores"],
                    user_stories=[
                        "As a commuter I want real-time wait data so that I can plan errands efficiently.",
                        "As a parent I want alerts before queues grow so that I can adjust schedules.",
                    ],
                    functional_requirements=[
                        "Crowdsourced check-in flow",
                        "Predictive wait-time charts",
                        "Notifications for threshold breaches",
                    ],
                    nonfunctional_requirements=["Responsive UI", "Accessible colour palette"],
                    success_metrics=["Weekly active users", "Reduction in wait time variance"],
                ),
                ready_for_prompt=True,
            )
        if output_model is crew_schemas.PromptResponse:
            return crew_schemas.PromptResponse(
                message="Here is your builder-ready prompt!",
                builder_prompt="Create a responsive queue intelligence dashboard with Tailwind styling...",
                follow_up="Need tweaks? Just say the word!",
            )
        raise AssertionError(f"Unexpected output model requested: {output_model}")

    monkeypatch.setattr("manager.crew.workflow.VentureBotCrew._execute_task", _fake_execute, raising=False)


def test_service_happy_path():
    print("🔍 CrewAI VentureBot Diagnostic")
    print("=" * 52)

    key_present = any(os.getenv(var) for var in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"))
    if key_present:
        print("✅ LLM API key detected in environment")
    else:
        print("⚠️ No LLM API key detected – real conversations will require GEMINI_API_KEY or another provider.")

    service = VentureBotService(config=VentureConfig(model="gemini/gemini-1.5-flash"))
    session = service.create_session(user_id="diagnostic-user")

    assert session["stage"] == "idea_generation"
    assert "VentureBot" in session["initial_message"]

    # Trigger idea generation
    ideas = service.chat(session["session_id"], "Let's begin")
    assert ideas["stage"] == "idea_selection"
    assert "Here are two concepts" in ideas["message"]

    # Select idea 1 -> should cascade through validation, PRD, and prompt generation
    final_response = service.chat(session["session_id"], "1")
    assert final_response["stage"] == "complete"
    assert "Validation complete" in final_response["message"]
    assert "builder-ready prompt" in final_response["message"]
    assert "BuilderPrompt" in final_response["memory"]

    print("🎉 CrewAI flow executed successfully with stubbed agents.")


if __name__ == "__main__":
    pytest.main([__file__])
