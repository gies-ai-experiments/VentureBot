import os
import yaml
import json
import anthropic
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from .sub_agents.product_manager.agent import product_manager
from .sub_agents.prompt_engineer.agent import prompt_engineer
from .sub_agents.idea_generator.agent import idea_generator
from .sub_agents.validator_agent.agent import validator_agent
from .sub_agents.onboarding_agent.agent import onboarding_agent
from google.adk.memory import Memory
from google.adk.memory.types import MemoryType
from google.adk.session import Session
# First check environment variables (prioritize --env-file in Docker)
api_key = os.getenv("ANTHROPIC_API_KEY")

# Only try to load from .env if environment variable is not set
if not api_key:
    try:
        dotenv_path = os.path.join(os.getcwd(), ".env")
        load_dotenv(dotenv_path)
        api_key = os.getenv("ANTHROPIC_API_KEY")
    except Exception as e:
        print(f"Note: .env file not found or error loading it: {e}")

# Verify API key is available
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Get the directory of the current file and load config
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.yaml")
cfg = yaml.safe_load(open(config_path))

# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=api_key)

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
    sub_agents=[idea_generator,validator_agent, product_manager, prompt_engineer, onboarding_agent],
    instruction=
    """
    You are a helpful orchestrator.
    
    Your job is to:
    - First, delegate to the onboarding agent to collect user information
    - Greet the user during onboarding, and ask for their name, interests, hobbies, etc. to understand their passions and tailor the ideas to their interests
    - If the user is not onboarded, delegate the task to the onboarding agent
    - Handle cases where user input is incomplete during onboarding:
        - If user doesn't provide a name, ask again with a friendly reminder
        -If user skips interests or hobbies, use default values and note this in memory
        -If user provides very short or unclear responses, ask for clarification
        - If user seems confused, provide examples of expected responses
    - Provide clear feedback for missing information
    - Allow users to skip optional fields
    - Access user profile from memory using MemoryType.USER_PROFILE
    - Access user preferences from memory using MemoryType.USER_PREFERENCES
    - Use this information to tailor the experience
    - Generate and refine ideas using the idea generator agent based on the user's interests you obtained during onboarding
    - Validate ideas using the validator agent
    - The idea generation and validation will be done in a loop until the idea is validated
    - After the idea is generated and validated, define a plan using the product manager agent
    - After the plan is approved by user, generate a prompt using the prompt engineer agent
    - Delegate the jobs and then regain control after completion of the task of the sub agent
    - If any agent fails or returns an error:
        - Log the error
        - Provide a user-friendly message
        - Attempt to recover gracefully
        - If recovery fails, restart the current step
    - Maintain conversation context throughout the entire workflow
    - Ensure smooth transitions between different agents
    """,
    description="An agent that manages the complete workflow by generating ideas and then defining a plan and the finally producing a prompt based on user input"
)

# Export the agent for ADK
__all__ = ["root_agent"]