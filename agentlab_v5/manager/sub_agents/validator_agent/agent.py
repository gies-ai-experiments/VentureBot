import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

from ...tools.tools import claude_web_search

dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env
# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the manager directory and get config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "manager", "config.yaml")
cfg = yaml.safe_load(open(config_path))

# Create Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ClaudeWebSearchValidator(Agent):
    """
    Validator agent that uses Claude's web search capability to evaluate ideas.
    Scores ideas based on feasibility and innovation using web search results.
    """
    async def handle(self, conversation, memory):
        print.info("Starting idea validation")
        ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
        scores = []
        for idea in ideas:
            print.debug(f"Validating idea: {idea['idea']}")
            # Use Claude web search function
            search_results = claude_web_search(idea["idea"],anthropic_client=anthropic_client)
            num_results = len(search_results.get("results", []))
            
            # Calculate scores based on search results
            feasibility = min(num_results/5, 1.0)
            innovation = max(1.0 - num_results/10, 0.0)
            final_score = feasibility * 0.6 + innovation * 0.4
            
            scores.append({
                "id": idea["id"],
                "feasibility": round(feasibility, 2),
                "innovation": round(innovation, 2),
                "score": round(final_score, 2),
            })
            print.debug(f"Score calculated: {scores[-1]}")
        return scores

# Create the validator agent
validator_agent = ClaudeWebSearchValidator(
    name="validator_agent",
    model=LiteLlm(model=cfg["model"]),
    instruction=(
        "You are an evaluator. For each idea, you'll use Claude's web search capability "
        "to look up existing solutions, then output "
        "a JSON list of scores: [{id, feasibility, innovation, score}, …]."
        "If the user asks about anything else, "
        "you should delegate the task to the manager agent."
    ),
    description="A specialized agent that validates ideas using web search to assess feasibility and innovation."
)