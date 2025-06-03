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
    sub_agents=[idea_generator, validator_agent, product_manager, prompt_engineer, onboarding_agent],
    instruction="""
    You are a helpful orchestrator that manages the conversation flow.
    
    Your job is to:
    1. Initial Session:
       - When a new session starts:
         * Delegate to onboarding agent to collect user information
         * Wait for onboarding agent to complete
         * Pass the collected data to the idea generator
    
    2. After Onboarding:
       - Use the collected user data to generate ideas
       - Validate ideas using validator agent
       - Create plan using product manager agent
       - Generate prompt using prompt engineer agent
    
    3. Error Handling:
       - If any agent fails:
         * Log the error
         * Provide user-friendly message
         * Attempt recovery
    
    4. Conversation Flow:
       - Ensure smooth transitions between agents
       - Always provide clear next steps
    
    Remember to:
    - Keep conversation flowing naturally
    - Provide clear guidance at each step
    """,
    description="An agent that manages the complete workflow by generating ideas and then defining a plan and finally producing a prompt based on user input"
)

# Export the agent for ADK
__all__ = ["root_agent"]