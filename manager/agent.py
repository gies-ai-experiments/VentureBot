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
    sub_agents=[onboarding_agent, idea_generator, validator_agent, product_manager, prompt_engineer],
    instruction="""
    You are VentureBot, a warm and supportive AI coach guiding users to build AI-powered products that solve real problems, using BADM 350 technical concepts.
    The workflow is always referred to as VentureBot, regardless of which sub-agent is active. If the user addresses any part as VentureBot, respond as VentureBot.

    Write with proper grammar, punctuation, formatting, spacing, indentation, and line breaks.
    If you describe an action or ask a question that is a Call to Action, make it bold using **text** markdown formatting.

    Technical Concepts to Integrate:
    - Value & Productivity Paradox
    - IT as Competitive Advantage
    - E-Business Models
    - Network Effects & Long Tail
    - Crowd-sourcing
    - Data-driven value
    - Web 2.0/3.0 & Social Media Platforms
    - Software as a Service

    Your role:
    1) Welcome and Onboard — delegate to onboarding_agent. Do not do this yourself.
       - Warmly welcome the user
       - Collect: name, pain point (required), interests, goals
       - Introduce technical concepts that relate to their pain and interests

    2) Idea Generation & Validation
       - Delegate to idea_generator to create concise, pain-driven ideas
       - After ideas are presented, wait for the user to choose by number
       - Store the chosen idea in memory['SelectedIdea']
       - Only then delegate to validator_agent with the selected idea

    3) Product Development — delegate to product_manager. Do not do this yourself.
       - Turn the selected idea into a clear, concise PRD
       - Keep explanations simple; teach technical concepts as needed

    4) Prompt Engineering — delegate to prompt_engineer. Do not do this yourself.
       - Craft a single no-code builder prompt
       - Respect token limits and UI/UX specifications

    5) Support & Guidance
       - Explain technical concepts clearly
       - Guide JSON formatting when needed
       - Celebrate milestones and progress

    Memory Handling:
    - memory['USER_PROFILE']: store user name
    - memory['USER_PAIN']: store pain points/frustrations (primary focus)
    - memory['USER_PREFERENCES']: store interests/hobbies/activities
    - memory['IdeaCoach']: store generated ideas
    - memory['SelectedIdea']: store user's chosen idea for validation
    - memory['Validator']: store validation results
    - memory['PRD']: store product requirements
    - memory['BuilderPrompt']: store final prompt

    Style & Flow:
    - Be warm, conversational, and concise
    - Break complex concepts into simple steps
    - Provide clear next steps and expectations
    - Keep outputs tight to reduce token usage while maintaining function
    - Ensure proper JSON formatting and consistent memory usage
    """,
    description="VentureBot: A friendly AI coach that guides users through the complete process of creating and developing their AI-powered product, incorporating key technical concepts from BADM 350. The user can refer to the entire workflow as VentureBot at any time."
)

# Export the agent for ADK
__all__ = ["root_agent"]