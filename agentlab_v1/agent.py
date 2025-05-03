
# agentlab_v2/agent.py

import yaml
import os
import requests
import time  # Import time module for timestamps
from google.adk.agents import Agent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
# No schema classes needed; rely on conversation history for context

# 1) Load your config file
cfg = yaml.safe_load(open("agentlab_v1/config.yaml"))

# 2) Create the leaf Agents
idea_agent = Agent(
    name="IdeaCoach",
    model=LiteLlm(model=cfg["model"]),
    instruction=(
        f"You are an idea coach. Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message."
    ),
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

product_manager = Agent(
    name="ProductManager",
    model=LiteLlm(model=cfg["model"]),
    instruction="You are a product manager: from the ideas and scores generated so far, select the single most valuable idea.",
)

prompt_engineer = Agent(
    name="PromptEngineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="Write a self-contained AI prompt that implements the chosen solution clearly and completely.",
)

# 3) Wrap Validator in a ParallelAgent (use sub_agents=...)
validation_agent = ParallelAgent(
    name="ValidateAll",
    sub_agents=[validator],
)

# 4) Chain brainstorming → validation → selection
gen_val_select = SequentialAgent(
    name="GenValidateSelect",
    sub_agents=[idea_agent, validation_agent, product_manager],
)

# 5) Loop a fixed number of times (ADK LoopAgent supports max_iterations only)
ensure_quality = LoopAgent(
    name="EnsureQuality",
    sub_agents=[gen_val_select],
    max_iterations=cfg["max_loops"],
)

# 6) Final pipeline: loop → prompt engineer
full_pipeline = SequentialAgent(
    name="FullWorkflow",
    sub_agents=[ensure_quality, prompt_engineer],
)

# 7) Expose the root agent for `adk web`
root_agent = full_pipeline