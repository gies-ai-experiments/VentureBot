import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

from ...tools.tools import claude_web_search

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the manager directory and get config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "manager", "config.yaml")
cfg = yaml.safe_load(open(config_path))
# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

idea_generator = Agent(
    name="idea_generator",
    model=LiteLlm(model=cfg["model"]),
    instruction=f"""
    Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message.
    If the user asks about anything else, 
    you should delegate the task to the manager agent.
    """,
    description="An LLM agent that generates creative ideas based on user input."
)