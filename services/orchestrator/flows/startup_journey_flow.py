from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from crewai import Agent, Task
from crewai.flow import Flow, listen, start
from crewai.flow.flow import FlowState
from pydantic import Field

REPO_ROOT = Path(__file__).resolve().parents[3]

# Add crew source directory to path
CREW_SRC_PATH = REPO_ROOT / "crewai-agents" / "src"
if CREW_SRC_PATH.exists() and str(CREW_SRC_PATH) not in sys.path:
    sys.path.append(str(CREW_SRC_PATH))

from venturebot_crew.crew import (  # noqa: E402
    VenturebotsAiEntrepreneurshipCoachingPlatformCrew,
)


CONTEXT_TO_STATE: Dict[str, str] = {
    "venturebot_user_onboarding_and_pain_point_discovery": "onboarding_summary",
    "venturebot_market_aware_idea_generation": "idea_slate",
    "comprehensive_market_validation": "validation_report",
    "venturebot_product_requirements_and_mvp_development": "prd_outline",
    "venturebot_no_code_builder_prompt_generation": "builder_prompt",
}


class StartupJourneyState(FlowState):
    """Flow state tracking VentureBots journey artefacts."""

    user_name: str = "Founder"
    industry_focus: str = "General entrepreneurship"
    startup_idea: str = ""
    conversation_text: str = ""
    completed_stages: List[str] = Field(default_factory=list)
    should_stop: bool = False

    onboarding_summary: Optional[str] = None
    idea_slate: Optional[str] = None
    validation_report: Optional[str] = None
    prd_outline: Optional[str] = None
    builder_prompt: Optional[str] = None
    entrepreneurship_plan: Optional[str] = None

    # Preserve raw inputs for templating inside tasks
    base_inputs: Dict[str, Any] = Field(default_factory=dict)


class StartupJourneyFlow(Flow[StartupJourneyState]):
    """CrewAI Flow orchestrating the entrepreneurship coaching pipeline."""

    initial_state = StartupJourneyState

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._blueprint = VenturebotsAiEntrepreneurshipCoachingPlatformCrew()
        self._agent_builders = {
            "venturebot_onboarding_agent": self._blueprint.venturebot_onboarding_agent,
            "venturebot_idea_generator": self._blueprint.venturebot_idea_generator,
            "market_validator_agent": self._blueprint.market_validator_agent,
            "venturebot_product_manager": self._blueprint.venturebot_product_manager,
            "venturebot_technical_prompt_engineer": self._blueprint.venturebot_technical_prompt_engineer,
        }
        self._task_builders = {
            "venturebot_user_onboarding_and_pain_point_discovery": self._blueprint.venturebot_user_onboarding_and_pain_point_discovery,
            "venturebot_market_aware_idea_generation": self._blueprint.venturebot_market_aware_idea_generation,
            "comprehensive_market_validation": self._blueprint.comprehensive_market_validation,
            "venturebot_product_requirements_and_mvp_development": self._blueprint.venturebot_product_requirements_and_mvp_development,
            "venturebot_no_code_builder_prompt_generation": self._blueprint.venturebot_no_code_builder_prompt_generation,
        }

    def _base_inputs(self) -> Dict[str, Any]:
        inputs = {
            "user_name": self.state.user_name,
            "industry_focus": self.state.industry_focus,
            "startup_idea": self.state.startup_idea,
        }
        if self.state.conversation_text:
            inputs["conversation_text"] = self.state.conversation_text
        self.state.base_inputs = inputs
        return inputs

    def _build_agent(self, agent_key: str) -> Agent:
        builder = self._agent_builders.get(agent_key)
        if builder is None:
            raise ValueError(f"No agent builder registered for '{agent_key}'.")
        return builder()

    def _build_task(self, task_key: str) -> Task:
        builder = self._task_builders.get(task_key)
        if builder is None:
            raise ValueError(f"No task builder registered for '{task_key}'.")
        return builder()

    def _context_payload(self, context_keys: Iterable[str]) -> Optional[str]:
        if isinstance(context_keys, str):
            normalized_context = [context_keys]
        elif isinstance(context_keys, Iterable):
            normalized_context = list(context_keys)
        else:
            normalized_context = []

        snippets: List[str] = []
        for ctx in normalized_context:
            state_attr = CONTEXT_TO_STATE.get(ctx)
            if not state_attr:
                continue
            value = getattr(self.state, state_attr, None)
            if value:
                snippets.append(f"{ctx}:\n{value}")
        if self.state.conversation_text:
            snippets.append(f"Conversation transcript:\n{self.state.conversation_text}")
        if not snippets:
            return None
        return "\n\n".join(snippets)

    def _run_task(self, task_key: str) -> str:
        task = self._build_task(task_key).model_copy(deep=True)

        agent_ref = task.agent
        if isinstance(agent_ref, str):
            agent = self._build_agent(agent_ref)
        elif isinstance(agent_ref, Agent):
            agent = agent_ref
        else:
            raise ValueError(f"Unsupported agent reference for task '{task_key}'.")

        # Assign the built agent to the task so EventBus can access agent.key
        task.agent = agent

        base_inputs = self._base_inputs()
        try:
            task.description = task.description.format(**base_inputs)
        except KeyError:
            # Leave description untouched if inputs missing
            pass
        if task.expected_output:
            try:
                task.expected_output = task.expected_output.format(**base_inputs)
            except KeyError:
                # Keep original expected_output if template variables are missing
                pass

        context_text = self._context_payload(getattr(task, "context", []))
        output = task.execute_sync(agent=agent, context=context_text)
        result_text = output.raw
        if not isinstance(result_text, str):
            result_text = str(result_text)
        return result_text.strip()

    @start()
    def onboarding(self) -> str:
        """Collect founder context and pain points."""
        if "onboarding_summary" in self.state.completed_stages:
            return "SKIPPED"
        if self.state.should_stop:
            return None

        onboarding_result = self._run_task("venturebot_user_onboarding_and_pain_point_discovery")
        self.state.onboarding_summary = onboarding_result
        self.state.should_stop = True
        return onboarding_result

    @listen("onboarding")
    def idea_generation(self, previous_output: str) -> str:
        """Produce market-aware idea slate."""
        if previous_output is None:
            return None
        if "idea_slate" in self.state.completed_stages:
            return "SKIPPED"
        if self.state.should_stop:
            return None

        idea_result = self._run_task("venturebot_market_aware_idea_generation")
        self.state.idea_slate = idea_result
        self.state.should_stop = True
        return idea_result

    @listen("idea_generation")
    def market_validation(self, previous_output: str) -> str:
        """Validate selected idea for feasibility."""
        if previous_output is None:
            return None
        if "validation_report" in self.state.completed_stages:
            return "SKIPPED"
        if self.state.should_stop:
            return None

        validation_result = self._run_task("comprehensive_market_validation")
        self.state.validation_report = validation_result
        self.state.should_stop = True
        return validation_result

    @listen("market_validation")
    def product_requirements(self, previous_output: str) -> str:
        """Craft detailed product requirements."""
        if previous_output is None:
            return None
        if "prd_outline" in self.state.completed_stages:
            return "SKIPPED"
        if self.state.should_stop:
            return None

        prd_result = self._run_task("venturebot_product_requirements_and_mvp_development")
        self.state.prd_outline = prd_result
        self.state.should_stop = True
        return prd_result

    @listen("product_requirements")
    def no_code_prompt(self, previous_output: str) -> str:
        """Translate requirements into a no-code builder prompt."""
        if previous_output is None:
            return None
        if "builder_prompt" in self.state.completed_stages:
            return "SKIPPED"
        if self.state.should_stop:
            return None

        builder_result = self._run_task("venturebot_no_code_builder_prompt_generation")
        self.state.builder_prompt = builder_result
        self.state.should_stop = True
        return builder_result

    @listen("no_code_prompt")
    def entrepreneurship_plan(self, previous_output: str) -> str:
        """Synthesize the entrepreneurship journey and next steps."""
        if previous_output is None:
            return None
        if "entrepreneurship_plan" in self.state.completed_stages:
            return "SKIPPED"
        if self.state.should_stop:
            return None

        # Journey orchestration handled by staged flow, return completion message
        plan_result = "🎉 Congratulations! You've completed the VentureBot journey."
        self.state.entrepreneurship_plan = plan_result
        self.state.should_stop = True
        return plan_result
