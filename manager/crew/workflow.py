"""Core workflow orchestration for the VentureBot CrewAI system."""
from __future__ import annotations

import re
import uuid
from dataclasses import asdict
from typing import Dict, Optional

from crewai import Crew, Process, Task
from pydantic import BaseModel

from manager.config import VentureConfig, load_config
from manager.crew.agents import build_agents
from manager.crew.schemas import (
    IdeaGenerationResponse,
    OnboardingResponse,
    ProductPlanResponse,
    PromptResponse,
    ValidationResponse,
)
from manager.crew.state import SessionState, Stage
from manager.crew.utils import dump_json, merge_memory, summarise_history


class VentureBotCrew:
    """High-level orchestrator that coordinates CrewAI agents per user session."""

    def __init__(self, config: Optional[VentureConfig] = None) -> None:
        self.config = config or load_config()
        self.agents = build_agents(self.config)
        self.sessions: Dict[str, SessionState] = {}

   
    def create_session(self, user_id: str) -> SessionState:
        """Initialise a new session and return its initial state."""
        session_id = str(uuid.uuid4())
        state = SessionState(session_id=session_id, user_id=user_id)
        self.sessions[session_id] = state
        # Bootstrap with welcome message from onboarding agent
        welcome = self._run_onboarding(state, latest_message=None, initial_call=True)
        state.append_history("assistant", welcome)
        return state

    def get_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            raise KeyError(f"Unknown session_id: {session_id}")
        return self.sessions[session_id]


    def handle_message(self, session_id: str, message: str) -> str:
        state = self.get_session(session_id)
        cleaned_message = message.strip()
        if cleaned_message:
            state.append_history("user", cleaned_message)

        responses: list[str] = []
        user_message_for_stage: Optional[str] = cleaned_message or None

        while True:
            progressed = False

            if state.stage == Stage.ONBOARDING:
                response = self._run_onboarding(state, latest_message=user_message_for_stage)
                responses.append(response)
                state.append_history("assistant", response)
                if state.stage == Stage.IDEA_GENERATION:
                    user_message_for_stage = None
                    progressed = True
                else:
                    break
            elif state.stage == Stage.IDEA_GENERATION:
                response = self._run_idea_generation(state)
                responses.append(response)
                state.append_history("assistant", response)
                break  # wait for idea selection
            elif state.stage == Stage.IDEA_SELECTION:
                selection_response = self._handle_idea_selection(state, user_message_for_stage)
                responses.append(selection_response)
                state.append_history("assistant", selection_response)
                if state.stage == Stage.VALIDATION:
                    user_message_for_stage = None
                    progressed = True
                else:
                    break
            elif state.stage == Stage.VALIDATION:
                response = self._run_validation(state)
                responses.append(response)
                state.append_history("assistant", response)
                if state.stage == Stage.PRODUCT_STRATEGY:
                    user_message_for_stage = None
                    progressed = True
                else:
                    break
            elif state.stage == Stage.PRODUCT_STRATEGY:
                response = self._run_product_manager(state, user_feedback=None)
                responses.append(response)
                state.append_history("assistant", response)
                if state.stage == Stage.PROMPT_ENGINEERING:
                    user_message_for_stage = None
                    progressed = True
                else:
                    break
            elif state.stage == Stage.PRODUCT_REFINEMENT:
                response = self._handle_product_refinement(state, user_message_for_stage)
                responses.append(response)
                state.append_history("assistant", response)
                if state.stage == Stage.PROMPT_ENGINEERING:
                    user_message_for_stage = None
                    progressed = True
                else:
                    break
            elif state.stage == Stage.PROMPT_ENGINEERING:
                response = self._run_prompt_engineer(state)
                responses.append(response)
                state.append_history("assistant", response)
                break
            else:  # COMPLETE or any fallback
                responses.append(
                    "🎉 **VentureBot Tip:** Let me know if you'd like to explore new ideas or iterate on the prompt!"
                )
                break

            if not progressed:
                break

        return "\n\n".join(filter(None, responses))

   
    def _execute_task(
        self,
        *,
        agent_key: str,
        description: str,
        expected_output: str,
        output_model: type[BaseModel],
        inputs: Optional[Dict[str, str]] = None,
    ) -> BaseModel:
        agent = self.agents[agent_key]
        task = Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            output_json=output_model,
            markdown=True,
        )
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
            memory=False,
        )
        result = crew.kickoff(inputs=inputs or {})
        task_output = result.tasks_output[-1]
        if task_output.pydantic:
            return task_output.pydantic
        if task_output.json_dict:
            return output_model.model_validate(task_output.json_dict)
        raise ValueError("Crew task did not return structured data")

    def _pending_fields(self, memory: Dict) -> list[str]:
        pending: list[str] = []
        profile = memory.get("USER_PROFILE", {}) or {}
        pain = memory.get("USER_PAIN", {}) or {}
        preferences = memory.get("USER_PREFERENCES", {}) or {}

        if not profile.get("name"):
            pending.append("USER_PROFILE.name")
        if not pain.get("description"):
            pending.append("USER_PAIN.description")
        if not pain.get("category"):
            pending.append("USER_PAIN.category (optional)")
        if not preferences.get("interests"):
            pending.append("USER_PREFERENCES.interests (optional)")
        if not preferences.get("activities"):
            pending.append("USER_PREFERENCES.activities (optional)")
        return pending

    def _run_onboarding(
        self,
        state: SessionState,
        *,
        latest_message: Optional[str],
        initial_call: bool = False,
    ) -> str:
        history_text = summarise_history(state.history)
        pending_fields = self._pending_fields(state.memory)
        profile = state.memory.get("USER_PROFILE", {}) or {}
        pain = state.memory.get("USER_PAIN", {}) or {}

        # If required details already exist, confirm and fast-forward to idea generation.
        if profile.get("name") and pain.get("description"):
            name = profile.get("name", "there")
            pain_desc = pain.get("description", "")
            message = (
                f"Hi {name}! I've got your pain point saved: \"{pain_desc}\". "
                "**Would you like me to generate a few ideas now?**"
            )
            state.stage = Stage.IDEA_GENERATION
            return message

        final_cta = (
            f"**Excellent! Next I'll generate {self.config.num_ideas} idea keys to fit the lock you described - ready?**"
        )
        description = (
            "You are VentureBot's onboarding specialist."
            "\n\nConversation history (most recent last):\n{history}\n\n"
            "Existing memory snapshot:\n{memory}\n\nPending fields:{pending}\n\n"
            "Latest user message:\n{message}\n\n"
            "Core responsibilities:\n"
            "- Introduce yourself as VentureBot and mention the user can call you VentureBot any time.\n"
            "- Highlight the key/lock metaphor: the idea is the key, the pain point is the lock it opens.\n"
            "- Share the mini-timeline: learn about you -> capture pain -> generate ideas -> you pick a favorite.\n"
            "- Use examples like Uber vs unreliable taxis or Netflix vs late fees to reinforce pain-driven innovation.\n"
            "- Prioritise required fields: USER_PROFILE.name and USER_PAIN.description. Ask for one item at a time.\n"
            "- For required items, if the reply is missing or 'skip', kindly ask again with encouragement.\n"
            "- Optional items: USER_PAIN.category (functional / social / emotional / financial), USER_PREFERENCES.interests, USER_PREFERENCES.activities.\n"
            "- When asking an optional question, append \"(type 'skip' to skip)\" so the user knows it's optional.\n"
            "- Extract new facts from the conversation and add them to memory_updates using the exact keys provided.\n"
            "- Celebrate helpful answers with short positive reinforcement (e.g. \"Great insight!\").\n"
            "- Keep responses concise, friendly, and well-formatted in markdown.\n"
            "- Do not expose raw JSON in the user message.\n"
            "- Mark ready_for_ideas as true only when name and pain description are populated in memory.\n"
            f"- When ready_for_ideas is true, close with the exact call-to-action: {final_cta}\n"
            "- Otherwise, end with a single clear follow-up question for the next missing detail."
        )
        expected_output = (
            "Return JSON using the OnboardingResponse schema with message, memory_updates, pending_fields,"
            " and ready_for_ideas populated according to the instructions."
        )
        inputs = {
            "history": history_text or "(no prior history)",
            "memory": dump_json(state.memory) if state.memory else "{}",
            "pending": "\n- " + "\n- ".join(pending_fields) if pending_fields else "\n- none",
            "message": latest_message or ("<<no user message>>" if initial_call else "<<silence>>"),
        }
        response = self._execute_task(
            agent_key="onboarding",
            description=description,
            expected_output=expected_output,
            output_model=OnboardingResponse,
            inputs=inputs,
        )
        # Update memory
        state.memory = merge_memory(state.memory, response.memory_updates)

        if response.ready_for_ideas:
            state.stage = Stage.IDEA_GENERATION
        else:
            state.stage = Stage.ONBOARDING
        return response.message

    def _run_idea_generation(self, state: SessionState) -> str:
        pain = state.memory.get("USER_PAIN", {})
        preferences = state.memory.get("USER_PREFERENCES", {})
        profile = state.memory.get("USER_PROFILE", {})
        founder = profile.get("name", "friend")
        pain_description = pain.get("description", "")
        pain_category = pain.get("category") or "unspecified"
        interests = preferences.get("interests", "")
        activities = preferences.get("activities", "")
        description = (
            "You are VentureBot's idea generator.\n"
            "\nInputs you MUST rely on:\n"
            f"- Founder name: {founder}\n"
            f"- Pain description: {pain_description or '<<missing>>'}\n"
            f"- Pain category: {pain_category}\n"
            f"- Interests: {interests or '<<none provided>>'}\n"
            f"- Activities: {activities or '<<none provided>>'}\n"
            "\nTechnical concepts to leverage (choose at least one per idea):\n"
            "- Value & Productivity Paradox\n"
            "- IT as Competitive Advantage\n"
            "- E-Business Models\n"
            "- Network Effects & Long Tail\n"
            "- Crowd-sourcing\n"
            "- Data-driven value\n"
            "- Web 2.0/3.0 & Social Media Platforms\n"
            "- Software as a Service\n"
            "\nRole & steps:\n"
            f"1) Generate {self.config.num_ideas} concise app ideas (≤ 15 words) that directly address the pain.\n"
            "2) Keep each idea practical for an initial build and avoid duplicates.\n"
            "3) Associate each idea with a short “Concept:” line naming the BADM 350 concept(s) used.\n"
            "4) Inspire the user while staying grounded in feasible execution.\n"
            "\nOutput formatting for the user message:\n"
            f"- Present a numbered list 1..{self.config.num_ideas}.\n"
            "- Each list item: one-line idea followed by a new line `Concept: <concept>`.\n"
            "- Do not expose raw JSON in the user-facing message.\n"
            "- End with the bold call-to-action **Reply with the number of the idea you want to validate next.**\n"
            "\nStructured response requirements:\n"
            "- Return JSON compliant with IdeaGenerationResponse.\n"
            "- Populate ideas with ids 1..{self.config.num_ideas}, each containing `idea` (≤ 15 words) and `concept`.\n"
            "- Ensure the `message` field matches the formatting instructions above."
        )
        expected_output = (
            "Return JSON matching IdeaGenerationResponse with the formatted user-facing message and idea list including id, idea text, and concept."
        )
        inputs = {
            "founder": founder,
            "pain": pain_description,
            "category": pain_category,
            "interests": interests,
            "activities": activities,
        }
        response = self._execute_task(
            agent_key="idea",
            description=description,
            expected_output=expected_output,
            output_model=IdeaGenerationResponse,
            inputs=inputs,
        )
        state.memory["IdeaCoach"] = [idea.model_dump() for idea in response.ideas]
        state.stage = Stage.IDEA_SELECTION
        return response.message

    def _handle_idea_selection(
        self, state: SessionState, user_message: Optional[str]
    ) -> str:
        if not user_message:
            return "**Please reply with the number of the idea you'd like me to validate.**"

        match = re.search(r"(\d+)", user_message)
        if not match:
            return "I didn't catch a number. Could you reply with the idea number (e.g., 2)?"

        selected_id = int(match.group(1))
        ideas = state.memory.get("IdeaCoach", [])
        selected = next((idea for idea in ideas if idea.get("id") == selected_id), None)
        if not selected:
            ids = ", ".join(str(idea.get("id")) for idea in ideas) or "1"
            return f"I couldn't find that idea. Please choose one of: {ids}."

        state.memory["SelectedIdea"] = selected
        state.stage = Stage.VALIDATION
        return f"Great choice! I'll evaluate idea {selected_id} next."

    def _run_validation(self, state: SessionState) -> str:
        selected = state.memory.get("SelectedIdea", {})
        pain = state.memory.get("USER_PAIN", {})
        description = (
            "You are VentureBot's market validator (legacy ADK-inspired)."
            "\n\nSelected idea: {idea}\nPain point: {pain}\nCategory: {category}\n\n"
            "Instructions:\n"
            "- Provide a concise evaluation grounded in business reasoning and BADM 350 concepts.\n"
            "- Consider multiple dimensions internally (e.g., market opportunity, competitive landscape,"
            " execution feasibility, innovation potential), but keep the final JSON to the provided schema.\n"
            "- Return short, helpful notes that explain the tradeoffs and potential next steps."
        )
        expected_output = (
            "Return JSON following ValidationResponse with message and score (feasibility, innovation, overall, notes)."
        )
        inputs = {
            "idea": selected.get("idea", ""),
            "pain": pain.get("description", ""),
            "category": pain.get("category") or "unspecified",
        }
        response = self._execute_task(
            agent_key="validator",
            description=description,
            expected_output=expected_output,
            output_model=ValidationResponse,
            inputs=inputs,
        )
        state.memory["Validator"] = response.score.model_dump()
        state.stage = Stage.PRODUCT_STRATEGY
        return response.message

    def _run_product_manager(
        self, state: SessionState, user_feedback: Optional[str]
    ) -> str:
        selected = state.memory.get("SelectedIdea", {})
        validation = state.memory.get("Validator", {})
        pain = state.memory.get("USER_PAIN", {})
        description = (
            "You are VentureBot's product strategist (legacy ADK PM mapping)."
            "\n\nSelected idea: {idea}\nPain point: {pain}\nValidation notes: {validation}\n"
            "User feedback (may be empty): {feedback}\n\n"
            "Create a clear PRD containing: overview, target users/personas, user stories, functional requirements,"
            " non-functional requirements, and success metrics. Keep it concise and readable. End with a bold CTA"
            " asking whether to refine or proceed to prompt engineering."
        )
        expected_output = (
            "Return JSON via ProductPlanResponse including message, prd sections, and ready_for_prompt boolean."
        )
        inputs = {
            "idea": selected.get("idea", ""),
            "pain": pain.get("description", ""),
            "validation": validation.get("notes", ""),
            "feedback": user_feedback or "",
        }
        response = self._execute_task(
            agent_key="product_manager",
            description=description,
            expected_output=expected_output,
            output_model=ProductPlanResponse,
            inputs=inputs,
        )
        state.memory["PRD"] = response.prd.model_dump()
        state.stage = Stage.PRODUCT_REFINEMENT
        if response.ready_for_prompt:
            state.stage = Stage.PROMPT_ENGINEERING
        return response.message

    def _handle_product_refinement(
        self, state: SessionState, user_message: Optional[str]
    ) -> str:
        if not user_message:
            return "**Let me know if you'd like to refine any section or say 'proceed' to move on to prompt engineering.**"

        lowered = user_message.lower()
        proceed_tokens = {"proceed", "continue", "next", "looks good", "go ahead"}
        if any(token in lowered for token in proceed_tokens):
            state.stage = Stage.PROMPT_ENGINEERING
            return "Perfect — I'll craft the no-code builder prompt now."

        # Otherwise treat as refinement feedback
        response = self._run_product_manager(state, user_feedback=user_message)
        return response

    def _run_prompt_engineer(self, state: SessionState) -> str:
        prd = state.memory.get("PRD", {})
        pain = state.memory.get("USER_PAIN", {})
        description = (
            "You are VentureBot's prompt engineer (legacy ADK prompt mapping)."
            "\n\nPRD JSON:{prd}\nPain point: {pain}\n\n"
            "Deliver a single builder-ready prompt for tools like Bolt.new or Lovable.\n"
            "Scope & structure:\n"
            "- Frontend-only (no backend).\n"
            "- Explicit screens and user flows.\n"
            "- UI components with key properties.\n"
            "- Interaction logic (events, transitions).\n"
            "- Modern, responsive UI guidance.\n"
            "- Briefly connect to relevant BADM 350 concepts when useful."
        )
        expected_output = (
            "Return JSON via PromptResponse with the user-facing message and builder_prompt string."
        )
        inputs = {
            "prd": dump_json(prd),
            "pain": pain.get("description", ""),
        }
        response = self._execute_task(
            agent_key="prompt_engineer",
            description=description,
            expected_output=expected_output,
            output_model=PromptResponse,
            inputs=inputs,
        )
        state.memory["BuilderPrompt"] = response.builder_prompt
        state.stage = Stage.COMPLETE
        message = response.message
        if response.follow_up:
            message = f"{message}\n\n{response.follow_up}"
        return message

    def snapshot(self, session_id: str) -> dict:
        state = self.get_session(session_id)
        data = asdict(state)
        data["stage"] = state.stage.value
        return data


__all__ = ["VentureBotCrew"]
