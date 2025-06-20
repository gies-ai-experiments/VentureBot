import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
from ...tools.tools import claude_web_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env
# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the agentlab_v5 directory and get config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config.yaml")
cfg = yaml.safe_load(open(config_path))

# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))



predictor_agent = Agent(
    name="predictor_agent", # Name of the agent 
    description="Predictor agent that uses MCP to predict future trends and market demand.",
    MODEL=LiteLlm(model=cfg["model"]),
    instruction="""
    You are VentureBot, a forward-thinking AI predictor agent that helps users forecast future trends and market demand, incorporating technical concepts from BADM 350 and modern UI/UX standards.
    The user may refer to you or the workflow as 'VentureBot' at any time, and you should always respond as VentureBot."""

    description="A predictor agent that uses MCP to predict future trends and market demand."
)