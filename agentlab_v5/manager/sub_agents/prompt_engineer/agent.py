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

# 6) Prompt generation
class ClaudePromptEngineer(Agent):
    """
    Prompt Engineer agent that creates AI prompts based on refined product concepts.
    Uses Claude to generate clear and effective prompts for implementation.
    """
    async def handle(self, conversation, memory):
        print.info("Starting prompt engineering phase")
        product_concept = memory["ProductManager"]
        
        try:
            response = anthropic_client.messages.create(
                model=cfg["model"],
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"Write a self-contained AI prompt that implements this product concept clearly:\n\n{product_concept}"
                    }
                ]
            )
            
            prompt = response.content[0].text
            print.info("Successfully generated prompt")
            return prompt
        
        except Exception as e:
            print.error(f"Error generating prompt: {str(e)}", exc_info=True)
            return f"Error generating prompt: {str(e)}"

prompt_engineer = ClaudePromptEngineer(
    name="prompt_engineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="""An agent that generates clear and effective AI prompts based on refined product concepts for creating a prototype on bolt.new.
    If the user asks about anything else, 
    you should delegate the task to the manager agent.
    """,
    description="An agent that generates clear and effective AI prompts based on refined product concepts for bolt.new"
)