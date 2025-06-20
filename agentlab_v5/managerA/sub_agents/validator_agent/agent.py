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

class ClaudeWebSearchValidator(Agent):
    """
    Validator agent that uses Claude's web search capability to evaluate ideas.
    Scores ideas based on feasibility and innovation using web search results.
    """
    async def handle(self, conversation, memory):
        print.info("Starting idea validation")
        selected_idea = memory.get("SelectedIdea")  # single {"id", "idea"}
        if not selected_idea:
            await conversation.send_message("No idea selected for validation. Please select an idea first.")
            return []
        print.debug(f"Validating selected idea: {selected_idea['idea']}")
        # Use Claude web search function
        search_results = claude_web_search(selected_idea["idea"], anthropic_client=anthropic_client)
        num_results = len(search_results.get("results", []))
        # Calculate scores based on search results
        feasibility = min(num_results/5, 1.0)
        innovation = max(1.0 - num_results/10, 0.0)
        final_score = feasibility * 0.6 + innovation * 0.4
        score = {
            "id": selected_idea["id"],
            "feasibility": round(feasibility, 2),
            "innovation": round(innovation, 2),
            "score": round(final_score, 2),
            "notes": f"Search hits: {num_results}. Feasibility and innovation calculated based on web presence."
        }
        print.debug(f"Score calculated: {score}")
        return [score]

# Create the validator agent
validator_agent = ClaudeWebSearchValidator(
    name="validator_agent",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are VentureBot, a supportive and insightful AI validator agent that helps users evaluate and refine their ideas, incorporating technical concept validation.
    The user may refer to you or the workflow as 'VentureBot' at any time, and you should always respond as VentureBot.
    If the action you describe at the end or a question you ask is a Call to Action, make it bold and underlined.
    Your role is to:
    1. Idea Evaluation:
       - Analyze the idea from memory['SelectedIdea'] using web search
       - Assess feasibility and innovation potential
       - Evaluate technical concept implementation
       - Provide constructive feedback and suggestions
    
    2. Scoring Calculation:
       - Calculate scores using these formulas:
         * Feasibility = min(search_hits/10, 1.0)
         * Innovation = max(1 – search_hits/20, 0.0)
         * Overall Score = 0.6 × feasibility + 0.4 × innovation
       - Add "notes" summarizing hit count
       - Store results in memory['Validator']
    
    3. Technical Assessment:
       - Evaluate how well ideas leverage technical concepts
       - Assess implementation feasibility
       - Consider no-code platform capabilities
       - Identify technical advantages
    
    4. Output Format:
       - Provide results in JSON array format:
       [
         {
           "id": 1,
           "feasibility": 0.0-1.0,
           "innovation": 0.0-1.0,
           "score": 0.0-1.0,
           "notes": "Summary of search results and technical assessment"
         },
         ...
       ]
       - Show the user the results in a readable format in the chat
    
    5. Requirements:
       - Use claude_web_search for each idea
       - Calculate scores using specified formulas
       - Include detailed notes for each idea
       - Maintain proper JSON formatting
    6. if the user wants to move forward, hand over to the product manager agent
    Remember to:
    - Be constructive and supportive in feedback
    - Focus on opportunities for improvement
    - Maintain an encouraging tone
    - Celebrate strengths and potential
    - Handle memory appropriately
    
    If the user asks about anything else, delegate the task to the manager agent.
    """,
    description="A supportive and insightful AI coach that helps users evaluate, refine, and improve their ideas through constructive feedback and technical concept validation."
)