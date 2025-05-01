# agentlab_v2/agent.py

import yaml
from google.adk.agents import Agent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
# No schema classes needed; rely on conversation history for context

# 1) Load your config file
cfg = yaml.safe_load(open("agentlab_v1/config.yaml"))

# 2) Create the leaf Agents
idea_agent = Agent(
    name="IdeaCoach",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction=(
        f"You are an idea coach. Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message."
    ),
)

validator = Agent(
    name="Validator",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction=(
        "You are an evaluator. Rate the last idea on a scale from 0.0 to 1.0. Reply with only the numeric score."
    ),
)

product_manager = Agent(
    name="ProductManager",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction="You are a product manager: from the ideas and scores generated so far, select the single most valuable idea.",
)

prompt_engineer = Agent(
    name="PromptEngineer",
    model=LiteLlm(model="openai/gpt-4o-mini"),
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