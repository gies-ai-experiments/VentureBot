import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from .sub_agents.product_manager.agent import product_manager
from .sub_agents.prompt_engineer.agent import prompt_engineer
from .sub_agents.idea_generator.agent import idea_generator
from .sub_agents.validator_agent.agent import validator_agent

# Load environment and config
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env

# Get the directory of the current file and load config
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.yaml")
cfg = yaml.safe_load(open(config_path))

# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

'''
idea_creator_and_validator = SequentialAgent(
    name="idea_creator_and_validator",
    sub_agents=[idea_generator,validator_agent],
    description="""Sequential agent that generates ideas and validates them by running the workflow multiple times if needed.
    It waits for user input after each response"""
)

ideator = LoopAgent(
    name="ideator",
    sub_agents=[idea_creator_and_validator],
    max_iterations=cfg.get("max_loops", 1),
    description="""A loop agent that generates ideas and validates them by running the workflow multiple times if needed.
    It waits for user input after each agent response and continues to next agent only if user approves the idea"""
)
'''


root_agent = Agent(
    name="manager",
    model=LiteLlm(model=cfg["model"]),
    sub_agents=[idea_generator,validator_agent, product_manager, prompt_engineer],
    instruction="""
    You are a helpful orchestrator.
    
    Your job is to:
    - Generate and refine ideas using the idea generator agent
    - Validate ideas using the validator agent
    - The idea generation and validation will be done in a loop until the idea is validated
    - After the idea is generated and validated, define a plan using the product manager agent
    - After the plan is approved by user, generate a prompt using the prompt engineer agent
    - Delegate the jobs and then regain control after completion of the task of the sub agent
    """,
    description="An agent that manages the complete workflow by generating ideas and then defining a plan and the finally producing a prompt based on user input"
)

# Export the agent for ADK
__all__ = ["root_agent"]