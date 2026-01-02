"""
Staged Journey Flow - Human-in-the-loop execution for VentureBots.

This module provides a stage-by-stage execution model where each agent
runs individually and waits for user input before proceeding to the next stage.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai import Agent, Task, Crew, Process
from openai import OpenAI

LOGGER = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]

# Add crew source directory to path
CREW_SRC_PATH = REPO_ROOT / "crewai-agents" / "src"
if CREW_SRC_PATH.exists() and str(CREW_SRC_PATH) not in sys.path:
    sys.path.append(str(CREW_SRC_PATH))

from venturebot_crew.crew import (  # noqa: E402
    VenturebotsAiEntrepreneurshipCoachingPlatformCrew,
)


class JourneyStage:
    """Constants for journey stages."""
    ONBOARDING = "onboarding"
    IDEA_GENERATION = "idea_generation"
    VALIDATION = "validation"
    PRD = "prd"
    PROMPT_ENGINEERING = "prompt_engineering"
    COMPLETE = "complete"


# Stage progression order
STAGE_ORDER = [
    JourneyStage.ONBOARDING,
    JourneyStage.IDEA_GENERATION,
    JourneyStage.VALIDATION,
    JourneyStage.PRD,
    JourneyStage.PROMPT_ENGINEERING,
    JourneyStage.COMPLETE,
]

# Map stages to their corresponding tasks
STAGE_TO_TASK = {
    JourneyStage.ONBOARDING: "venturebot_user_onboarding_and_pain_point_discovery",
    JourneyStage.IDEA_GENERATION: "venturebot_market_aware_idea_generation",
    JourneyStage.VALIDATION: "comprehensive_market_validation",
    JourneyStage.PRD: "venturebot_product_requirements_and_mvp_development",
    JourneyStage.PROMPT_ENGINEERING: "venturebot_no_code_builder_prompt_generation",
}

# Map stages to context keys for state storage
STAGE_TO_CONTEXT_KEY = {
    JourneyStage.ONBOARDING: "onboarding_summary",
    JourneyStage.IDEA_GENERATION: "idea_slate",
    JourneyStage.VALIDATION: "validation_report",
    JourneyStage.PRD: "prd_outline",
    JourneyStage.PROMPT_ENGINEERING: "builder_prompt",
}


@dataclass
class StageContext:
    """Context accumulated across stages."""
    user_name: str = "Founder"
    industry_focus: str = "General entrepreneurship"
    startup_idea: str = ""
    user_message: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    # Stage outputs
    onboarding_summary: Optional[str] = None
    idea_slate: Optional[str] = None
    validation_report: Optional[str] = None
    prd_outline: Optional[str] = None
    builder_prompt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary for storage."""
        return {
            "user_name": self.user_name,
            "industry_focus": self.industry_focus,
            "startup_idea": self.startup_idea,
            "onboarding_summary": self.onboarding_summary,
            "idea_slate": self.idea_slate,
            "validation_report": self.validation_report,
            "prd_outline": self.prd_outline,
            "builder_prompt": self.builder_prompt,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageContext":
        """Deserialize context from dictionary."""
        return cls(
            user_name=data.get("user_name", "Founder"),
            industry_focus=data.get("industry_focus", "General entrepreneurship"),
            startup_idea=data.get("startup_idea", ""),
            onboarding_summary=data.get("onboarding_summary"),
            idea_slate=data.get("idea_slate"),
            validation_report=data.get("validation_report"),
            prd_outline=data.get("prd_outline"),
            builder_prompt=data.get("builder_prompt"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "StageContext":
        """Deserialize from JSON string."""
        if not json_str:
            return cls()
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            return cls()


@dataclass
class StageResult:
    """Result from running a single stage."""
    stage: str
    output: str
    next_stage: str
    context: StageContext
    is_complete: bool = False


class StagedJourneyExecutor:
    """
    Executor for running individual stages of the VentureBots journey.
    
    This class provides methods to run a single stage at a time,
    accumulating context between stages and returning control to the caller
    after each stage completes.
    """
    
    def __init__(self) -> None:
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
    
    def _build_agent(self, agent_key: str) -> Agent:
        """Build an agent from the blueprint."""
        builder = self._agent_builders.get(agent_key)
        if builder is None:
            raise ValueError(f"No agent builder registered for '{agent_key}'.")
        return builder()
    
    def _build_task(self, task_key: str) -> Task:
        """Build a task from the blueprint."""
        builder = self._task_builders.get(task_key)
        if builder is None:
            raise ValueError(f"No task builder registered for '{task_key}'.")
        return builder()
    
    def _get_base_inputs(self, context: StageContext) -> Dict[str, Any]:
        """Get base inputs for task interpolation."""
        return {
            "user_name": context.user_name,
            "industry_focus": context.industry_focus,
            "startup_idea": context.startup_idea,
        }

    def _run_onboarding_direct(self, context: StageContext) -> str:
        """Run onboarding using direct LLM call (faster than CrewAI)."""
        # Build conversation history
        history_text = ""
        if context.conversation_history:
            history_text = "\n".join([
                f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}"
                for msg in context.conversation_history[-10:]
            ])

        prompt = f"""You are "The Warm Guide" having a CONVERSATION with the user.

CONVERSATION FLOW (determine where user is based on history):
1. No info shared yet → Welcome warmly with the key/lock metaphor, ask for their name AND main frustration in one question
   Example: "Welcome to VentureBot! I'm here to help you discover a startup idea. Think of it this way: a great idea is like a key, and a real pain point is the lock it opens. What's your name, and what's something that frustrates you or wastes your time regularly?"
2. Name and pain shared → Briefly acknowledge and offer to generate ideas immediately
   Example: "Great to meet you, [name]! [Pain] sounds like a real problem worth solving. Ready for me to generate some startup ideas that could tackle this?"

RULES:
- Respond ONLY to what the user just said
- Keep responses under 50 words
- Be warm, use their name once you know it
- Use the key/lock metaphor in the first message
- Move quickly to idea generation - don't ask too many questions
- If user shares name AND pain point together, immediately offer to generate ideas

Recent conversation:
{history_text}

User's latest message: {context.user_message}

Respond with a short message (under 50 words):"""

        try:
            client = OpenAI()
            # Use gpt-4o for direct calls (gpt-5-mini has API restrictions)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
            )
            result = response.choices[0].message.content.strip()
            LOGGER.info(f"Direct onboarding response (gpt-4o): {result[:100]}...")
            return result
        except Exception as e:
            LOGGER.error(f"Direct onboarding failed: {e}")
            return "Welcome to VentureBot! What's your name, and what frustrates you most?"

    def _run_idea_generation_direct(self, context: StageContext) -> str:
        """Run idea generation using direct LLM call (faster than CrewAI)."""
        # Get onboarding context
        onboarding_summary = context.onboarding_summary or ""

        # Build conversation history for context
        history_text = ""
        if context.conversation_history:
            history_text = "\n".join([
                f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}"
                for msg in context.conversation_history[-6:]
            ])

        prompt = f"""You are "The Creative Catalyst." Generate exactly 5 startup ideas based on the user's pain points.

CONTEXT FROM ONBOARDING:
{onboarding_summary}

RECENT CONVERSATION:
{history_text}

REQUIREMENTS:
- Generate exactly 5 ideas (not more, not fewer)
- Each idea must be ≤15 words
- Each must directly address their specific pain point
- Each must include a business model (SaaS, marketplace, network effects, data-driven, etc.)

OUTPUT FORMAT:
Start with: "Here are 5 keys that could open your lock:"

1. **[Idea Name]**: [One-line description]. Business model: [Type]
2. **[Idea Name]**: [One-line description]. Business model: [Type]
3. **[Idea Name]**: [One-line description]. Business model: [Type]
4. **[Idea Name]**: [One-line description]. Business model: [Type]
5. **[Idea Name]**: [One-line description]. Business model: [Type]

End with: "**Reply with the number of the idea you'd like to explore.**"

Generate the 5 ideas now:"""

        try:
            client = OpenAI()
            # Use gpt-4o for direct calls (gpt-5-mini has API restrictions)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=500,
            )
            result = response.choices[0].message.content.strip()
            LOGGER.info(f"Direct idea generation response (gpt-4o): {result[:100]}...")
            return result
        except Exception as e:
            LOGGER.error(f"Direct idea generation failed: {e}")
            return "I encountered an issue generating ideas. Could you tell me more about your pain point?"

    def _detect_stage_transition_intent(
        self,
        user_message: str,
        current_stage: str,
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Use LLM to detect if user wants to proceed to next stage.

        Returns a dict with:
            - should_proceed: bool
            - confidence: float (0.0-1.0)
            - reason: str
        """
        next_stage = self.get_next_stage(current_stage)
        next_stage_display = next_stage.replace("_", " ").title()
        current_stage_display = current_stage.replace("_", " ").title()

        # Format recent conversation for context
        recent_history = conversation_history[-6:] if conversation_history else []
        history_text = "\n".join([
            f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')[:200]}"
            for msg in recent_history
        ]) if recent_history else "No previous conversation"

        prompt = f"""Analyze the user's message and conversation context to determine their intent.

Current stage: {current_stage_display}
Next stage: {next_stage_display}

Recent conversation:
{history_text}

User's latest message: "{user_message}"

Determine if the user wants to PROCEED to the next stage ({next_stage_display}) or CONTINUE with the current stage.

Signs user wants to proceed (be generous - when in doubt, proceed):
- Expressing readiness or satisfaction with current stage
- Asking to see results, ideas, or validation
- Indicating they've shared enough information
- Explicitly asking to move forward or skip ahead
- Saying things like "let's move on", "what's next", "I'm ready", "yes", "sure", "ok", "go ahead"
- Responding affirmatively to an offer to generate ideas
- Any positive or agreeing response after sharing their pain point

Signs user wants to continue current stage:
- Explicitly asking follow-up questions about current topic
- Explicitly wanting to explore more or add more details
- Asking clarifying questions about the process

IMPORTANT: Bias towards proceeding. If the user has shared their name and a pain point, and gives any affirmative or positive response, they likely want to proceed.

Respond with JSON only (no markdown, no code blocks):
{{"should_proceed": true or false, "confidence": 0.0 to 1.0, "reason": "brief explanation"}}"""

        try:
            client = OpenAI()
            # Use gpt-4o-mini for intent detection (lightweight, fast, reliable)
            intent_model = "gpt-4o-mini"

            response = client.chat.completions.create(
                model=intent_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,
            )

            result_text = response.choices[0].message.content
            if result_text is None:
                LOGGER.warning("Intent detection returned None content")
                return {"should_proceed": False, "confidence": 0.0, "reason": "Empty response"}

            result_text = result_text.strip()
            LOGGER.info(f"Intent detection raw response: {result_text[:200]}")

            # Clean up potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()

            result = json.loads(result_text)
            LOGGER.info(f"Intent detection result: {result}")
            return result

        except Exception as e:
            LOGGER.warning(f"Intent detection failed: {e}, defaulting to no transition")
            return {"should_proceed": False, "confidence": 0.0, "reason": f"Detection failed: {e}"}

    def _build_context_text(self, context: StageContext, current_stage: str) -> str:
        """
        Build context text from previous stages to inform the current agent.
        
        This provides the agent with all relevant information from previous
        stages to maintain continuity in the conversation.
        """
        snippets: List[str] = []
        
        # Add user's latest message
        if context.user_message:
            snippets.append(f"User's latest message:\n{context.user_message}")
        
        # Add conversation history
        if context.conversation_history:
            history_text = "\n".join([
                f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}"
                for msg in context.conversation_history[-10:]  # Last 10 messages
            ])
            snippets.append(f"Recent conversation:\n{history_text}")
        
        # Add outputs from previous stages based on current stage
        stage_index = STAGE_ORDER.index(current_stage) if current_stage in STAGE_ORDER else 0
        
        for i, stage in enumerate(STAGE_ORDER[:stage_index]):
            context_key = STAGE_TO_CONTEXT_KEY.get(stage)
            if context_key:
                value = getattr(context, context_key, None)
                if value:
                    snippets.append(f"Output from {stage}:\n{value}")
        
        combined_context = "\n\n---\n\n".join(snippets) if snippets else ""
        LOGGER.info(f"Built context for stage {current_stage} with length {len(combined_context)}")
        return combined_context
    
    def _run_task(
        self,
        task_key: str,
        context: StageContext,
        current_stage: str,
    ) -> str:
        """Execute a single task and return its output."""
        task = self._build_task(task_key).model_copy(deep=True)
        
        # Get the agent for this task
        agent_ref = task.agent
        if isinstance(agent_ref, str):
            agent = self._build_agent(agent_ref)
            # Ensure agent has a key attribute for EventBus
            if not hasattr(agent, 'key') or agent.key is None:
                agent.key = agent_ref
        elif isinstance(agent_ref, Agent):
            agent = agent_ref
            # Ensure agent has a key attribute for EventBus
            if not hasattr(agent, 'key') or agent.key is None:
                agent.key = task_key
        else:
            raise ValueError(f"Unsupported agent reference for task '{task_key}'.")
        
        # Assign agent to task
        task.agent = agent
        
        # WORKAROUND: Assign a dummy crew to agent to prevent Telemetry error
        # The error 'NoneType object has no attribute key' happens because 
        # on_task_started event listener tries to access agent.crew.key
        if not getattr(agent, "crew", None):
            # Create a lightweight dummy crew
            dummy_crew = Crew(
                agents=[agent], 
                tasks=[task], 
                process=Process.sequential,
                verbose=True
            )
            agent.crew = dummy_crew
        
        # Interpolate task description with inputs
        base_inputs = self._get_base_inputs(context)
        try:
            task.description = task.description.format(**base_inputs)
        except KeyError:
            pass  # Leave unchanged if interpolation fails
        
        if task.expected_output:
            try:
                task.expected_output = task.expected_output.format(**base_inputs)
            except KeyError:
                # Keep original expected_output if template variables are missing
                pass
        
        # Build context from previous stages
        context_text = self._build_context_text(context, current_stage)
        
        # Execute the task with explicit agent
        output = task.execute_sync(agent=agent, context=context_text)
        result_text = output.raw
        if not isinstance(result_text, str):
            result_text = str(result_text)
        
        cleaned_result = result_text.strip()
        if not cleaned_result:
            LOGGER.warning(f"Task {task_key} returned empty output.")
            cleaned_result = "I have completed the task, but I don't have any specific output to show. Let's proceed."

        LOGGER.info(f"Task {task_key} output: {cleaned_result[:100]}...")
        return cleaned_result
    
    def get_next_stage(self, current_stage: str) -> str:
        """Get the next stage after the current one."""
        try:
            current_index = STAGE_ORDER.index(current_stage)
            if current_index + 1 < len(STAGE_ORDER):
                return STAGE_ORDER[current_index + 1]
        except ValueError:
            # Current stage not in STAGE_ORDER, treat as complete
            pass
        return JourneyStage.COMPLETE
    
    def run_stage(
        self,
        stage: str,
        context: StageContext,
    ) -> StageResult:
        """
        Run a single stage of the journey.
        
        Args:
            stage: The stage to run (e.g., 'onboarding', 'idea_generation')
            context: The accumulated context from previous stages
            
        Returns:
            StageResult containing the output and updated context
        """
        if stage == JourneyStage.COMPLETE:
            return StageResult(
                stage=stage,
                output="🎉 Congratulations! You've completed the full VentureBot journey. "
                       "Would you like to start a new venture exploration or refine any previous step?",
                next_stage=JourneyStage.COMPLETE,
                context=context,
                is_complete=True,
            )
        
        task_key = STAGE_TO_TASK.get(stage)
        if not task_key:
            LOGGER.error(f"Unknown stage: {stage}")
            return StageResult(
                stage=stage,
                output="I'm sorry, I encountered an unexpected state. Let's start fresh.",
                next_stage=JourneyStage.ONBOARDING,
                context=context,
                is_complete=False,
            )
        
        try:
            # Run the task for this stage
            # Use direct LLM for fast stages, CrewAI for complex stages
            if stage == JourneyStage.ONBOARDING:
                output = self._run_onboarding_direct(context)
            elif stage == JourneyStage.IDEA_GENERATION:
                output = self._run_idea_generation_direct(context)
            else:
                # Use CrewAI for complex stages (validation, PRD, prompt engineering)
                output = self._run_task(task_key, context, stage)

            # Store the output in context
            context_key = STAGE_TO_CONTEXT_KEY.get(stage)
            if context_key:
                setattr(context, context_key, output)

            # Determine next stage based on LLM intent detection
            # For onboarding, use LLM to understand if user wants to proceed
            if stage == JourneyStage.ONBOARDING:
                # Require minimum context before considering transition
                has_minimum_context = (
                    context.onboarding_summary is not None and
                    len(context.conversation_history) >= 1  # At least 1 exchange
                )

                if has_minimum_context and context.user_message:
                    # Use LLM to detect user's intent
                    intent = self._detect_stage_transition_intent(
                        context.user_message,
                        stage,
                        context.conversation_history,
                    )

                    should_proceed = intent.get("should_proceed", False)
                    confidence = intent.get("confidence", 0.0)

                    if should_proceed and confidence >= 0.5:
                        next_stage = self.get_next_stage(stage)
                        LOGGER.info(f"Transitioning from {stage} to {next_stage} (confidence: {confidence})")
                        # Don't auto-run next stage - let it run on next user message
                    else:
                        # Stay in onboarding for more conversation
                        next_stage = JourneyStage.ONBOARDING
                else:
                    # Not enough context yet, stay in onboarding
                    next_stage = JourneyStage.ONBOARDING
            else:
                next_stage = self.get_next_stage(stage)

            # Only show "Next Stage" footer when actually transitioning (non-auto cases)
            if next_stage != stage and next_stage != JourneyStage.COMPLETE:
                next_stage_display = next_stage.replace("_", " ").title()
                if next_stage == JourneyStage.PRD:
                    next_stage_display = "Product Requirements (PRD)"
                elif next_stage == JourneyStage.VALIDATION:
                    next_stage_display = "Market Validation"

                output += f"\n\n---\n\n**Next Stage: {next_stage_display}**\n\nPlease let me know when you are ready to proceed."

            return StageResult(
                stage=stage,
                output=output,
                next_stage=next_stage,
                context=context,
                is_complete=(next_stage == JourneyStage.COMPLETE),
            )
            
        except Exception as exc:
            LOGGER.exception(f"Error running stage {stage}: {exc}")
            return StageResult(
                stage=stage,
                output=f"I encountered an issue while processing. Let me try a different approach. "
                       f"Could you please share more details about what you're looking for?",
                next_stage=stage,  # Stay on same stage for retry
                context=context,
                is_complete=False,
            )
    
    def run_onboarding_auto(self, context: StageContext) -> StageResult:
        """
        Auto-run the onboarding stage when a new session starts.
        
        This is called when a session is first created to automatically
        kick off the onboarding process without waiting for user input.
        """
        return self.run_stage(JourneyStage.ONBOARDING, context)


# Global executor instance for reuse
_executor: Optional[StagedJourneyExecutor] = None


def get_executor() -> StagedJourneyExecutor:
    """Get or create the global executor instance."""
    global _executor
    if _executor is None:
        _executor = StagedJourneyExecutor()
    return _executor
