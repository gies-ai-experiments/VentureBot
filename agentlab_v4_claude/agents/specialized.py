from typing import Dict, Any, List
from google.adk.agents import Agent, BaseAgent
from google.adk.models.lite_llm import LiteLlm
from ..tools.web_search import claude_web_search

class ClaudeWebSearchValidator(Agent):
    """Agent that validates ideas using Claude's web search capability."""
    
    async def handle(self, conversation, memory):
        ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
        scores = []
        for idea in ideas:
            # Use Claude web search function
            search_results = claude_web_search(idea["idea"])
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
        return scores

class UserIdeaProcessor(Agent):
    """Agent that processes user-provided ideas."""
    
    async def handle(self, conversation, memory):
        user_input = memory.get("user_idea_input", "")
        
        # If user typed 'proceed', we'll show them the generated ideas
        if user_input.lower() == "proceed":
            return {"proceed_to_suggestions": True}
        else:
            # User provided their own idea
            return {"proceed_to_suggestions": False, "user_idea": user_input}

class ClaudeWebSearchProductManager(Agent):
    """Agent that manages idea selection and processing."""
    
    async def handle(self, conversation, memory):
        # Check if we have a user-provided idea from UserIdeaProcessor
        processor_result = memory.get("UserIdeaProcessor", {})
        proceed_to_suggestions = processor_result.get("proceed_to_suggestions", True)
        
        if not proceed_to_suggestions:
            # User provided their own idea
            user_idea = processor_result.get("user_idea", "")
            selected_idea = {"id": 0, "idea": user_idea}
        else:
            # User selected from suggestions
            ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
            selected_id = int(memory["user_input"])  # User selected ID
            
            # Find the selected idea
            selected_idea = next((idea for idea in ideas if idea["id"] == selected_id), None)
        
        if not selected_idea:
            return "Selected idea not found."
        
        return selected_idea

class ClaudePromptEngineer(Agent):
    """Agent that engineers the final prompt based on the selected idea."""
    
    async def handle(self, conversation, memory):
        selected_idea = memory.get("ProductManager", {})
        if not selected_idea:
            return "No idea selected for prompt engineering."
            
        # Use Claude to generate a self-contained prompt
        return {
            "prompt": f"Create a detailed implementation plan for: {selected_idea['idea']}",
            "idea_id": selected_idea["id"]
        }

class ClaudeFeedbackAgent(Agent):
    """Agent that provides feedback and improvements for ideas."""
    
    async def handle(self, conversation, memory):
        selected_idea = memory.get("ProductManager", {})
        if not selected_idea:
            return "No idea selected for feedback."
            
        # Use Claude to provide feedback and improvements
        return {
            "feedback": f"Analysis and improvements for: {selected_idea['idea']}",
            "idea_id": selected_idea["id"]
        } 