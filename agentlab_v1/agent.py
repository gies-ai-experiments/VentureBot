import os
import requests
import yaml
from dotenv import load_dotenv
from typing import AsyncGenerator
from typing_extensions import override
from pydantic import Field
from google.adk.agents import Agent, BaseAgent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from pydantic import Field
import logging
logging.basicConfig(level=logging.INFO)

# # Load environment and config
# dotenv_path = os.path.join(os.getcwd(), ".env")
# load_dotenv(dotenv_path)  # loads SERPAPI_KEY from .env
# cfg = yaml.safe_load(open("agentlab_v1/config.yaml"))

# # Tool: SerpAPI search
# def serpapi_search(query: str):
#     res = requests.get(
#         f"https://serpapi.com/search.json?q={query}&api_key={os.getenv('SERPAPI_KEY')}"
#     )
#     return res.json().get("organic_results", [])

# 1) Load your config file
cfg = yaml.safe_load(open("agentlab_v1/config.yaml"))

# 1) Idea generation
idea_agent = Agent(
    name="IdeaCoach",
    model=LiteLlm(model=cfg["model"]),
    instruction=f"Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message.",
)

class SerpApiValidator(Agent):
    async def handle(self, conversation, memory):
        ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
        scores = []
        for idea in ideas:
            results = serpapi_search(idea["idea"])
            feasibility = min(len(results)/10, 1.0)
            innovation  = max(1.0 - len(results)/20, 0.0)
            final_score = feasibility * 0.6 + innovation * 0.4
            scores.append({
                "id": idea["id"],
                "feasibility": round(feasibility, 2),
                "innovation": round(innovation, 2),
                "score": round(final_score, 2),
            })
        return scores

# Create the validator agent
validator = SerpApiValidator(
    name="Validator",
    model=LiteLlm(model=cfg["model"]),
    instruction=(
        "You are an evaluator. For each idea, use the provided "
        "`serpapi_search` tool to look up existing solutions, then output "
        "a JSON list of scores: [{id, feasibility, innovation, score}, …]."
    ),
)


# 3) Generic InputAgent for human input


# Modify the InputAgent implementation to use a custom memory key
def InputAgentFactory(name: str, prompt: str, memory_key: str = "user_input") -> BaseAgent:
    class InputAgent(BaseAgent):
        prompt: str = Field(description="User prompt text")
        memory_key: str = Field(description="Memory key to store input")
        model_config = {"arbitrary_types_allowed": True}

        def __init__(self, name: str, prompt: str, memory_key: str):
            super().__init__(name=name, sub_agents=[], prompt=prompt, memory_key=memory_key)
            self.memory_key = memory_key

        @override
        async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
            # --- If this invocation carries the user's reply, capture it ---
            # Fix for AttributeError: 'InvocationContext' object has no attribute 'invocation'
            # Assuming the correct structure based on the error suggestion
            if hasattr(ctx, 'initial_user_content') and ctx.initial_user_content:
                user_msg = ctx.initial_user_content.parts[0].text
                ctx.session.state[self.memory_key] = user_msg
                yield Event(content={self.memory_key: user_msg})
                # Don't end the invocation here - let the pipeline continue to the next agent
                # Set end_invocation to False explicitly to ensure pipeline continues
                ctx.end_invocation = False
                return

            # --- Otherwise, send the prompt and pause the pipeline ---
            yield Event(content=self.prompt)
            # Pause the pipeline to wait for user input
            ctx.end_invocation = True

    return InputAgent(name=name, prompt=prompt, memory_key=memory_key)


# We don't need pre_product_input since we want the workflow to continue automatically
# after the user selects an idea ID without requiring additional input

# 4) Use InputAgent to capture idea selection
to_selection = InputAgentFactory(
    name="UserSelector",
    prompt="Select idea ID to proceed from the validated list:"
)

# 5) Product refinement based on human input
product_manager = Agent(
    name="ProductManager",
    model=LiteLlm(model=cfg["model"]),
    instruction="Refine and develop the idea indexed by memory['user_input'] from memory['IdeaCoach'].",
)

# 6) Prompt generation
to_prompt = Agent(
    name="PromptEngineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="Write a self-contained AI prompt that implements the product concept clearly.",
)

# 7) Pipeline assembly
gen_val_select = SequentialAgent(
    name="GenValidateSelect",
    sub_agents=[idea_agent, validator, to_selection, product_manager, to_prompt],
)

# Define ensure_quality first
ensure_quality = LoopAgent(
    name="EnsureQuality",
    sub_agents=[gen_val_select],
    max_iterations=cfg.get("max_loops", 1),
)

# Define feedback_agent
feedback_agent = Agent(
    name="FeedbackAgent",
    model=LiteLlm(model=cfg["model"]),
    instruction="Process feedback on the product concept.",
)

#Then define full_pipeline (only once)
full_pipeline = SequentialAgent(
    name="FullWorkflow",
    sub_agents=[ensure_quality, feedback_agent]#, to_prompt],
)

# Expose root agent
root_agent = full_pipeline