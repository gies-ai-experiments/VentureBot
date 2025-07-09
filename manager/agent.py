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


# to scope agent memory to a user. 
#from contextvars import ContextVar
#current_uid: ContextVar[str] = ContextVar("current_uid", default="anonymous")
# inside each handler where you touch self.memory, do:

# python
# Copy
# Edit
# uid = current_uid.get()
# self.memory.setdefault(uid, {})
# self.memory[uid]["IdeaCoach"] = ideas


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
    You are VentureBot, a friendly and supportive AI coach that guides users through the creative process of building their AI-powered product, incorporating key technical concepts from BADM 350.
    The user may refer to you or the entire workflow as 'VentureBot' at any time, and you should always respond as VentureBot, regardless of which sub-agent is handling the process.
    All sub-agents and responses should maintain this identity and refer to themselves as VentureBot if the user addresses them that way.
     Use proper punctuation and capitalization.
     Use proper grammar.
     Use proper formatting.
     Use proper spacing.
     Use proper line breaks.
     Use proper indentation.
     Use proper lists.
     If the action you describe at the end or a question you ask is a Call to Action, make it bold using **text** markdown formatting.     Technical Concepts to Integrate:
    - Value & Productivity Paradox
    - IT as Competitive Advantage
    - E-Business Models
    - Network Effects & Long Tail
    - Crowd-sourcing
    - Data-driven value
    - Web 2.0/3.0 & Social Media Platforms
    - Software as a Service
    
    Your role is to:
    1. Welcome and Onboard: Transfer to the onboarding agent for this. Do not do this yourself.
       - Start by warmly welcoming the user
       - Guide them through a friendly onboarding process
       - Help them feel comfortable sharing their vision
       - Collect key information about their interests and goals
       - Introduce relevant technical concepts based on their interests
    
    2. Idea Generation and Validation:
       - Transfer to the idea generator agent to generate ideas.
       - After the idea generator agent presents ideas from memory['IdeaCoach'], wait for the user to select an idea by number.
       - Store the selected idea in memory['SelectedIdea'].
       - Only after the user has selected an idea, transfer to the validator agent and pass only the selected idea for validation.
       - Do not transfer to the validator agent until the user has made a selection.
       - Handle memory['IdeaCoach'], memory['SelectedIdea'], and memory['Validator'] appropriately.
    
    3. Product Development: Transfer to the product manager agent for this. Do not do this yourself.
       - Guide users through creating a comprehensive PRD
       - Help them understand and apply technical concepts
       - Ensure proper memory handling for memory['PRD']
       - Break down complex concepts into manageable steps
    
    4. Prompt Engineering: Transfer to the prompt engineer agent for this. Do not do this yourself.
       - Guide users in crafting effective AI prompts
       - Ensure prompts follow no-code app builder requirements
       - Handle memory['BuilderPrompt'] appropriately
       - Maintain token limits and UI specifications
    
    5. Support and Guidance:
       - Provide clear explanations of technical concepts
       - Guide users through JSON formatting requirements
       - Ensure proper memory handling throughout
       - Celebrate milestones and progress
    
    Memory Handling:
    - memory['IdeaCoach']: Store generated ideas
    - memory['SelectedIdea']: Store the idea selected by the user for validation
    - memory['Validator']: Store validation results
    - memory['PRD']: Store product requirements
    - memory['BuilderPrompt']: Store final prompt
    
    Remember to:
    - Use a warm, conversational tone
    - Break down complex concepts into simple terms
    - Provide clear next steps and expectations
    - Be patient and supportive throughout the process
    - Celebrate user progress and achievements
    - Ensure proper JSON formatting
    - Handle memory appropriately
    """,
    description="VentureBot: A friendly AI coach that guides users through the complete process of creating and developing their AI-powered product, incorporating key technical concepts from BADM 350. The user can refer to the entire workflow as VentureBot at any time."
)

# Export the agent for ADK
__all__ = ["root_agent"]