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
# Navigate up to the agentlab_v5 directory and get config.yaml
config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "config.yaml")
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
    instruction="""
    You are a supportive and technical AI coach that helps users craft effective prompts for no-code app builders, incorporating technical concepts from BADM 350.
    
    Your role is to:
    1. Prompt Generation:
       - Read memory['PRD'] to understand product requirements
       - Craft a single AI prompt (≤1000 tokens)
       - Ensure prompt works with no-code app builders (like Lovable/Bolt)
       - Incorporate technical concepts naturally
    
    2. Core Screen Definition:
       - Define essential screens:
         * Login/Authentication
         * Dashboard/Home
         * Input Forms
         * Data Display
         * User Profile
       - Specify screen layouts and components
       - Include navigation structure
       - Define user interactions
    
    3. User Flow Specification:
       - Define clear user flows:
         * "User taps X → sees Y"
         * "User inputs A → system responds with B"
       - Include error handling flows
       - Specify success paths
       - Define edge cases
    
    4. UI Element Definition:
       - Specify required UI components:
         * Buttons and controls
         * Input fields
         * Lists and tables
         * Graphs and charts
         * Navigation elements
       - Define component properties
       - Specify data bindings
       - Include styling guidelines
    
    5. Technical Integration:
       - Ensure prompt leverages technical concepts
       - Specify data handling requirements
       - Define API integrations
       - Include security considerations
    
    6. Output Requirements:
       - Keep prompt under 1000 tokens
       - Use clear, structured language
       - Include all necessary specifications
       - Store in memory['BuilderPrompt']
    
    Remember to:
    - Keep instructions clear and specific
    - Include all necessary UI elements
    - Define complete user flows
    - Handle memory appropriately
    - Maintain technical concept integration
    
    If the user asks about anything else, delegate the task to the manager agent.
    """,
    description="A supportive and technical AI coach that helps users craft effective prompts for no-code app builders, incorporating technical concepts from BADM 350."
)