import os
import requests
import yaml
import anthropic
from dotenv import load_dotenv
from typing import AsyncGenerator, Dict, Any
from typing_extensions import override
from pydantic import Field
from google.adk.agents import Agent, BaseAgent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
import logging

logging.basicConfig(level=logging.INFO)

# Load environment and config
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env
cfg = yaml.safe_load(open("agentlab_claude_websearch/config.yaml"))

# Initialize Anthropic client for Claude 3.7 Sonnet with web search capability
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Define web search tool for Claude
web_search_tool = {
    "name": "search_internet",
    "description": "Search the internet for latest information on a topic",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on the internet",
            }
        },
        "required": ["query"],
    }
}

# Custom function for web search using Claude
def claude_web_search(query: str) -> Dict[str, Any]:
    """
    Use Claude's native web search functionality to search the web
    """
    try:
        # Initial message with the search query
        message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219", 
            max_tokens=1000,
            tools=[web_search_tool],
            messages=[
                {
                    "role": "user",
                    "content": f"Search the web for information about: {query}"
                }
            ]
        )
        
        # Handle tool use if Claude decides to use the search tool
        if hasattr(message, 'stop_reason') and message.stop_reason == "tool_use":
            tool_use = next((c for c in message.content if getattr(c, 'type', None) == 'tool_use'), None)
            if tool_use:
                tool_name = tool_use.name
                tool_params = tool_use.input
                tool_id = tool_use.id
                
                # Continue the conversation to get search results
                search_response = anthropic_client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Search the web for information about: {query}"
                        },
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "I'll search the web for information on this topic."
                                },
                                {
                                    "type": "tool_use",
                                    "name": tool_name,
                                    "id": tool_id,
                                    "input": tool_params
                                }
                            ]
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "result": f"Please provide search results for: {query}"
                                }
                            ]
                        }
                    ]
                )
                
                # Extract text content from the response
                results = []
                for i, content in enumerate(search_response.content):
                    if getattr(content, 'type', None) == "text":
                        results.append({"title": f"Result {i+1}", "content": content.text, "position": i+1})
                
                return {"results": results}
        
        # Handle direct response (no tool use)
        text_content = next((c for c in message.content if getattr(c, 'type', None) == 'text'), None)
        if text_content:
            return {"results": [{"title": "Direct Response", "content": text_content.text, "position": 1}]}
        
        return {"results": []}
    
    except Exception as e:
        logging.error(f"Error in claude_web_search: {str(e)}")
        return {"results": []}

# 1) Idea generation
idea_agent = Agent(
    name="IdeaCoach",
    model=LiteLlm(model=cfg["model"]),
    instruction=f"Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message.",
)

class ClaudeWebSearchValidator(Agent):
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

# Create the validator agent
validator = ClaudeWebSearchValidator(
    name="Validator",
    model=LiteLlm(model=cfg["model"]),
    instruction=(
        "You are an evaluator. For each idea, you'll use Claude's web search capability "
        "to look up existing solutions, then output "
        "a JSON list of scores: [{id, feasibility, innovation, score}, …]."
    ),
)

# 3) Generic InputAgent for human input
def InputAgentFactory(name: str, prompt: str, memory_key: str = "user_input") -> BaseAgent:
    class InputAgent(BaseAgent):
        prompt: str = Field(description="User prompt text")
        memory_key: str = Field(description="Memory key to store input")
        model_config = {"arbitrary_types_allowed": True}

        def __init__(self, name: str, prompt: str, memory_key: str):
            super().__init__(name=name, sub_agents=[], prompt=prompt, memory_key=memory_key)
            self.memory_key = memory_key

        @override
        async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
            # --- If this invocation carries the user's reply, capture it ---
            if hasattr(ctx, 'initial_user_content') and ctx.initial_user_content:
                user_msg = ctx.initial_user_content.parts[0].text
                ctx.session.state[self.memory_key] = user_msg
                yield Event(content={self.memory_key: user_msg})
                # Don't end the invocation here - let the pipeline continue to the next agent
                ctx.end_invocation = False
                return

            # --- Otherwise, send the prompt and pause the pipeline ---
            yield Event(content=self.prompt)
            # Pause the pipeline to wait for user input
            ctx.end_invocation = True

    return InputAgent(name=name, prompt=prompt, memory_key=memory_key)

# 4) Use InputAgent to capture idea selection
to_selection = InputAgentFactory(
    name="UserSelector",
    prompt="Select idea ID to proceed from the validated list:"
)

class ClaudeWebSearchProductManager(Agent):
    async def handle(self, conversation, memory):
        ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
        selected_id = int(memory["user_input"])  # User selected ID
        
        # Find the selected idea
        selected_idea = None
        for idea in ideas:
            if idea["id"] == selected_id:
                selected_idea = idea
                break
        
        if not selected_idea:
            return "Selected idea not found."
        
        # Use Claude web search to get additional context
        search_results = claude_web_search(selected_idea["idea"])
        
        # Format search results for Claude
        search_context = ""
        if search_results and "results" in search_results:
            search_context = "\n\nWeb Search Context:\n"
            for i, result in enumerate(search_results["results"]):
                search_context += f"{i+1}. {result.get('title', 'Result')}: {result.get('content', '')}\n"
        
        # Use Claude 3.7 Sonnet to refine the idea
        try:
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": f"Refine and develop this idea: {selected_idea['idea']}{search_context}"
                    }
                ]
            )
            
            refined_idea = response.content[0].text
            return refined_idea
        
        except Exception as e:
            logging.error(f"Error refining idea: {str(e)}")
            return f"Error refining idea: {str(e)}"

# 5) Product refinement based on human input with Claude's web search
product_manager = ClaudeWebSearchProductManager(
    name="ProductManager",
    model=LiteLlm(model=cfg["model"]),
    instruction="Refine and develop the idea indexed by memory['user_input'] from memory['IdeaCoach'] using Claude's web search for additional context.",
)

# 6) Prompt generation
class ClaudePromptEngineer(Agent):
    async def handle(self, conversation, memory):
        product_concept = memory["ProductManager"]
        
        try:
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"Write a self-contained AI prompt that implements this product concept clearly:\n\n{product_concept}"
                    }
                ]
            )
            
            prompt = response.content[0].text
            return prompt
        
        except Exception as e:
            logging.error(f"Error generating prompt: {str(e)}")
            return f"Error generating prompt: {str(e)}"

to_prompt = ClaudePromptEngineer(
    name="PromptEngineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="Write a self-contained AI prompt that implements the product concept clearly using Claude 3.7 Sonnet.",
)

# 7) Pipeline assembly
gen_val_select = SequentialAgent(
    name="GenValidateSelect",
    sub_agents=[idea_agent, validator, to_selection, product_manager, to_prompt],
)

# Define ensure_quality first
ensure_quality = LoopAgent(
    name="EnsureQuality",
    sub_agents=[gen_val_select],
    max_iterations=cfg.get("max_loops", 1),
)

# Define feedback_agent with Claude web search capability
class ClaudeFeedbackAgent(Agent):
    async def handle(self, conversation, memory):
        product_concept = memory["ProductManager"]
        prompt = memory["PromptEngineer"]
        
        # This will be populated from user input in a real workflow
        feedback = "Please improve this concept further."
        
        try:
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                tools=[web_search_tool],
                messages=[
                    {
                        "role": "user",
                        "content": f"Here's a product concept:\n\n{product_concept}\n\nHere's the prompt:\n\n{prompt}\n\nHere's some feedback: {feedback}\n\nPlease revise the concept based on this feedback. Use web search if needed for additional information."
                    }
                ]
            )
            
            revised_concept = response.content[0].text
            return revised_concept
        
        except Exception as e:
            logging.error(f"Error processing feedback: {str(e)}")
            return f"Error processing feedback: {str(e)}"

feedback_agent = ClaudeFeedbackAgent(
    name="FeedbackAgent",
    model=LiteLlm(model=cfg["model"]),
    instruction="Process feedback on the product concept using Claude 3.7 Sonnet with web search capability.",
)

# Then define full_pipeline
full_pipeline = SequentialAgent(
    name="FullWorkflow",
    sub_agents=[ensure_quality, feedback_agent],
)

# Expose root agent
root_agent = full_pipeline