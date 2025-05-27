import os
import requests
import yaml
import anthropic
from dotenv import load_dotenv
from typing import AsyncGenerator, Dict, Any, Optional
from typing_extensions import override
from pydantic import Field
from google.adk.agents import Agent, BaseAgent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
import logging

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment and config
dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)  # loads ANTHROPIC_API_KEY from .env
cfg = yaml.safe_load(open("agentlab_v4_claude/config.yaml"))

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
    
    Args:
        query (str): The search query to look up
        
    Returns:
        Dict[str, Any]: Search results with title and content
    """
    try:
        logger.info(f"Performing web search for query: {query}")
        # Initial message with the search query
        message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219", 
            max_tokens=4000,
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
                
                logger.debug(f"Tool use detected: {tool_name} with params: {tool_params}")
                
                # Continue the conversation to get search results
                search_response = anthropic_client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=5000,
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
                
                logger.info(f"Found {len(results)} search results")
                return {"results": results}
        
        # Handle direct response (no tool use)
        text_content = next((c for c in message.content if getattr(c, 'type', None) == 'text'), None)
        if text_content:
            logger.info("Received direct response without tool use")
            return {"results": [{"title": "Direct Response", "content": text_content.text, "position": 1}]}
        
        return {"results": []}
    
    except Exception as e:
        logger.error(f"Error in claude_web_search: {str(e)}", exc_info=True)
        return {"results": []}

# Define InputAgentFactory first
def InputAgentFactory(name: str, prompt: str, memory_key: str = "user_input") -> BaseAgent:
    """
    Factory function to create input agents that handle user interaction.
    
    Args:
        name (str): Name of the agent
        prompt (str): Prompt to show to the user
        memory_key (str): Key to store user input in memory
        
    Returns:
        BaseAgent: Configured input agent
    """
    class InputAgent(BaseAgent):
        prompt: str = Field(description="User prompt text")
        memory_key: str = Field(description="Memory key to store input")
        model_config = {"arbitrary_types_allowed": True}

        def __init__(self, name: str, prompt: str, memory_key: str):
            super().__init__(name=name, sub_agents=[], prompt=prompt, memory_key=memory_key)
            self.memory_key = memory_key

        @override
        async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
            logger.info(f"InputAgent {self.name} starting execution")
            # --- If this invocation carries the user's reply, capture it ---
            if hasattr(ctx, 'initial_user_content') and ctx.initial_user_content:
                user_msg = ctx.initial_user_content.parts[0].text
                ctx.session.state[self.memory_key] = user_msg
                logger.debug(f"Captured user input: {user_msg}")
                yield Event(content={self.memory_key: user_msg})
                # Don't end the invocation here - let the pipeline continue to the next agent
                ctx.end_invocation = False
                return

            # --- Otherwise, send the prompt and pause the pipeline ---
            logger.debug(f"Sending prompt: {self.prompt}")
            yield Event(content=self.prompt)
            # Pause the pipeline to wait for user input
            ctx.end_invocation = True

    return InputAgent(name=name, prompt=prompt, memory_key=memory_key)

# 1) Idea generation
idea_agent = Agent(
    name="IdeaCoach",
    model=LiteLlm(model=cfg["model"]),
    instruction=f"Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message.",
    description="An LLM agent that generates creative ideas based on user input. Uses Claude 3.7 Sonnet to brainstorm innovative concepts."
)

# 2) Input agent for user's own idea
to_idea_input = InputAgentFactory(
    name="UserIdeaInput",
    prompt="Please enter your own idea or type 'proceed' to view the generated suggestions:",
    memory_key="user_idea_input"
)

class ClaudeWebSearchValidator(Agent):
    """
    Validator agent that uses Claude's web search capability to evaluate ideas.
    Scores ideas based on feasibility and innovation using web search results.
    """
    async def handle(self, conversation, memory):
        logger.info("Starting idea validation")
        ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
        scores = []
        for idea in ideas:
            logger.debug(f"Validating idea: {idea['idea']}")
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
            logger.debug(f"Score calculated: {scores[-1]}")
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
    description="A specialized agent that validates ideas using web search to assess feasibility and innovation."
)

# Create an agent to process the user idea input
class UserIdeaProcessor(Agent):
    """
    Agent that processes user-provided ideas and determines workflow direction.
    Handles both custom user ideas and generated suggestions.
    """
    async def handle(self, conversation, memory):
        logger.info("Processing user idea input")
        user_input = memory.get("user_idea_input", "")
        
        # If user typed 'proceed', we'll show them the generated ideas
        if user_input.lower() == "proceed":
            logger.debug("User chose to proceed with generated ideas")
            return {"proceed_to_suggestions": True}
        else:
            # User provided their own idea
            logger.debug(f"User provided custom idea: {user_input}")
            return {"proceed_to_suggestions": False, "user_idea": user_input}

user_idea_processor = UserIdeaProcessor(
    name="UserIdeaProcessor",
    model=LiteLlm(model=cfg["model"]),
    instruction="Process the user's idea input and determine next steps.",
    description="An agent that processes user input to determine whether to use generated ideas or custom user ideas."
)

# 4) Use InputAgent to capture idea selection
to_selection = InputAgentFactory(
    name="UserSelector",
    prompt="Select idea ID to proceed from the validated list:"
)

class ClaudeWebSearchProductManager(Agent):
    """
    Product Manager agent that refines ideas using Claude's web search capability.
    Integrates web search results to enhance and develop product concepts.
    """
    async def handle(self, conversation, memory):
        logger.info("Starting product management phase")
        # Check if we have a user-provided idea from UserIdeaProcessor
        processor_result = memory.get("UserIdeaProcessor", {})
        proceed_to_suggestions = processor_result.get("proceed_to_suggestions", True)
        
        if not proceed_to_suggestions:
            # User provided their own idea
            user_idea = processor_result.get("user_idea", "")
            selected_idea = {"id": 0, "idea": user_idea}
            logger.debug(f"Using user-provided idea: {user_idea}")
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
            
            logger.debug(f"Selected idea from suggestions: {selected_idea}")
        
        if not selected_idea:
            logger.error("Selected idea not found")
            return "Selected idea not found."
        
        # Use Claude web search to get additional context
        search_results = claude_web_search(selected_idea["idea"])
        
        # Format search results for Claude
        search_context = ""
        if search_results and "results" in search_results:
            search_context = "\n\nWeb Search Context:\n"
            for i, result in enumerate(search_results["results"]):
                search_context += f"{i+1}. {result.get('title', 'Result')}: {result.get('content', '')}\n"
        
        logger.debug(f"Generated search context: {search_context[:100]}...")
        
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
            logger.info("Successfully refined idea")
            return refined_idea
        
        except Exception as e:
            logger.error(f"Error refining idea: {str(e)}", exc_info=True)
            return f"Error refining idea: {str(e)}"

# 5) Product refinement based on human input with Claude's web search
product_manager = ClaudeWebSearchProductManager(
    name="ProductManager",
    model=LiteLlm(model=cfg["model"]),
    instruction="Refine and develop the idea indexed by memory['user_input'] from memory['IdeaCoach'] using Claude's web search for additional context.",
    description="A specialized agent that refines product ideas using web search and Claude's capabilities to enhance concepts."
)

# 6) Prompt generation
class ClaudePromptEngineer(Agent):
    """
    Prompt Engineer agent that creates AI prompts based on refined product concepts.
    Uses Claude to generate clear and effective prompts for implementation.
    """
    async def handle(self, conversation, memory):
        logger.info("Starting prompt engineering phase")
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
            logger.info("Successfully generated prompt")
            return prompt
        
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}", exc_info=True)
            return f"Error generating prompt: {str(e)}"

to_prompt = ClaudePromptEngineer(
    name="PromptEngineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="Write a self-contained AI prompt that implements the product concept clearly using Claude 3.7 Sonnet.",
    description="An agent that generates clear and effective AI prompts based on refined product concepts."
)

# Create a conditional flow manager
class ConditionalFlowManager(BaseAgent):
    """
    Flow Manager that orchestrates the entire workflow.
    Handles conditional logic and agent sequencing based on user input.
    """
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info("Starting workflow execution")
        try:
            # Run the idea generation first
            async for event in idea_agent.run_async(ctx):
                yield event
            
            # Ask for user input
            async for event in to_idea_input.run_async(ctx):
                yield event
            
            # Process the user input
            async for event in user_idea_processor.run_async(ctx):
                yield event
            
            # Get the decision from the processor
            processor_result = ctx.session.state.get("UserIdeaProcessor", {})
            proceed_to_suggestions = processor_result.get("proceed_to_suggestions", True)
            
            if proceed_to_suggestions:
                logger.debug("Proceeding with generated suggestions")
                # User wants to see suggestions, run validator
                async for event in validator.run_async(ctx):
                    yield event
                
                # Then let them select an idea
                async for event in to_selection.run_async(ctx):
                    yield event
            
            # Run the product manager
            async for event in product_manager.run_async(ctx):
                yield event
            
            # Finally, generate the prompt
            async for event in to_prompt.run_async(ctx):
                yield event
            
            logger.info("Workflow completed successfully")
            yield Event(content="Workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
            yield Event(content=f"Error in workflow: {str(e)}")

# Create the flow manager
flow_manager = ConditionalFlowManager(
    name="FlowManager",
    sub_agents=[idea_agent, to_idea_input, user_idea_processor, validator, to_selection, product_manager, to_prompt],
    description="The main workflow orchestrator that manages the sequence of agents and handles conditional logic."
)

# Define ensure_quality first
ensure_quality = LoopAgent(
    name="EnsureQuality",
    sub_agents=[flow_manager],
    max_iterations=cfg.get("max_loops", 1),
    description="A loop agent that ensures quality by running the workflow multiple times if needed."
)

# Define feedback_agent with Claude web search capability
class ClaudeFeedbackAgent(Agent):
    """
    Feedback Agent that provides improvements and suggestions using Claude's web search.
    Integrates web search results to enhance feedback quality.
    """
    async def handle(self, conversation, memory):
        logger.info("Starting feedback phase")
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
            logger.info("Successfully generated feedback")
            return revised_concept
        
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            return f"Error processing feedback: {str(e)}"

feedback_agent = ClaudeFeedbackAgent(
    name="FeedbackAgent",
    model=LiteLlm(model=cfg["model"]),
    instruction="Process feedback on the product concept using Claude 3.7 Sonnet with web search capability.",
    description="An agent that provides feedback and improvements using Claude's web search capabilities."
)

# Then define full_pipeline
root_agent = SequentialAgent(
    name="agentlab_v4_claude",
    sub_agents=[ensure_quality, feedback_agent],
    description="The complete workflow pipeline that combines quality assurance and feedback generation."
)
