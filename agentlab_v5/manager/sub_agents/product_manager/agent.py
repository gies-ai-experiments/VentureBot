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

class ClaudeWebSearchProductManager(Agent):
    """
    Product Manager agent that refines ideas using Claude's web search capability.
    Integrates web search results to enhance and develop product concepts.
    """
    async def handle(self, conversation, memory):
        print.info("Starting product management phase")
        # Check if we have a user-provided idea from UserIdeaProcessor
        processor_result = memory.get("UserIdeaProcessor", {})
        proceed_to_suggestions = processor_result.get("proceed_to_suggestions", True)
        
        if not proceed_to_suggestions:
            # User provided their own idea
            user_idea = processor_result.get("user_idea", "")
            selected_idea = {"id": 0, "idea": user_idea}
            print.debug(f"Using user-provided idea: {user_idea}")
        else:
            # User selected from suggestions
            ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
            selected_id = int(memory["user_input"])  # User selected ID
            
            # Find the selected idea
            selected_idea = None
            for idea in ideas:
                if idea["id"] == selected_id:
                    selected_idea = idea
                    break
            
            print.debug(f"Selected idea from suggestions: {selected_idea}")
        
        if not selected_idea:
            print.error("Selected idea not found")
            return "Selected idea not found."
        
        # Use Claude web search to get additional context
        search_results = claude_web_search(selected_idea["idea"], anthropic_client)
        
        # Format search results for Claude
        search_context = ""
        if search_results and "results" in search_results:
            search_context = "\n\nWeb Search Context:\n"
            for i, result in enumerate(search_results["results"]):
                search_context += f"{i+1}. {result.get('title', 'Result')}: {result.get('content', '')}\n"
        
        print.debug(f"Generated search context: {search_context[:100]}...")
        
        # Use Claude 3.7 Sonnet to refine the idea
        try:
            response = anthropic_client.messages.create(
                model=cfg["model"],
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": f"Refine and develop this idea: {selected_idea['idea']}{search_context}"
                    }
                ]
            )
            
            refined_idea = response.content[0].text
            print.info("Successfully refined idea")
            return refined_idea
        
        except Exception as e:
            print.error(f"Error refining idea: {str(e)}", exc_info=True)
            return f"Error refining idea: {str(e)}"

# 5) Product refinement based on human input with Claude's web search
product_manager = ClaudeWebSearchProductManager(
    name="product_manager",
    model=LiteLlm(model=cfg["model"]),
    instruction="""Refine and develop the idea indexed by memory['user_input'] from memory['IdeaCoach'] using Claude's web search for additional context.
    If the user asks about anything else, 
    you should delegate the task to the manager agent.
    """,
    description="A specialized agent that refines product ideas and generates a plan using web search to enhance concepts."
)