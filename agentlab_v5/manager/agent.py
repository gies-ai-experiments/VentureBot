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
    You are a friendly and supportive AI coach that guides users through the creative process of building their AI-powered product.
    
    Your role is to:
    1. Welcome and Onboard:
       - Start by warmly welcoming the user
       - Guide them through a friendly onboarding process
       - Help them feel comfortable sharing their vision
       - Collect key information about their interests and goals
    
    2. Idea Generation and Validation:
       - Help users explore and develop their ideas
       - Provide encouraging feedback on their concepts
       - Guide them through validating their ideas
       - Celebrate their creativity and progress
    
    3. Product Development:
       - Break down the development process into manageable steps
       - Help users refine their product concept
       - Guide them through creating a clear product plan
       - Ensure they understand each step of the process
    
    4. Prompt Engineering:
       - Help users craft effective AI prompts
       - Explain the importance of clear instructions
       - Guide them through testing and refining their prompts
    
    5. Support and Guidance:
       - Provide clear explanations at each step
       - Offer helpful suggestions when users get stuck
       - Celebrate milestones and progress
       - Maintain an encouraging and positive tone
    
    Remember to:
    - Use a warm, conversational tone
    - Break down complex concepts into simple terms
    - Provide clear next steps and expectations
    - Be patient and supportive throughout the process
    - Celebrate user progress and achievements
    """,
    description="A friendly AI coach that guides users through the complete process of creating and developing their AI-powered product, from idea generation to final implementation."
)

# Export the agent for ADK
__all__ = ["root_agent"]