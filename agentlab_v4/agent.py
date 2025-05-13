import logging
from typing import AsyncGenerator
from typing_extensions import override
import yaml
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent, BaseAgent, SequentialAgent, Agent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event
from pydantic import BaseModel
from typing import List, Optional, Callable
from pydantic import ConfigDict
 
# 1) Load your config file
cfg = yaml.safe_load(open("agentlab_v4/config.yaml"))
 
 
# --- Root Agent with Human-in-the-Loop ---
class RootAgent(BaseAgent):
    """
    Root agent that manages human-in-the-loop interactions.
    """
    # Required fields for Google ADK compatibility
    name: str
    sub_agents: List[BaseAgent]
    workflow_agent: BaseAgent
    before_agent_callback: Optional[Callable] = None
    after_agent_callback: Optional[Callable] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, workflow_agent: BaseAgent):
        super().__init__(
            name="RootAgent",
            sub_agents=[workflow_agent],
            workflow_agent=workflow_agent,
            before_agent_callback=None,
            after_agent_callback=None
        )
        object.__setattr__(self, 'workflow_agent', workflow_agent)
 
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        while True:
            async for event in self.workflow_agent.run_async(ctx):
                yield event
            
            # Check if we have generated ideas
            if "generated_ideas" in ctx.session.state:
                print("\n--- Generated Ideas ---")
                for i, idea in enumerate(ctx.session.state["generated_ideas"], 1):
                    print(f"{i}. {idea}")
                
                choice = input("\nOptions:\n1. Regenerate ideas\n2. Continue with these ideas\n3. Exit\nChoose (1-3): ")
                
                if choice == "1":
                    ctx.session.state.pop("generated_ideas", None)
                    continue
                elif choice == "3":
                    return
            
            # Similar checks for other stages can be added here
            if "product_prd" in ctx.session.state:
                print("\n--- Generated PRD ---")
                print(ctx.session.state["product_prd"])
                
                choice = input("\nOptions:\n1. Regenerate PRD\n2. Continue\n3. Exit\nChoose (1-3): ")
                
                if choice == "1":
                    ctx.session.state.pop("product_prd", None)
                    continue
                elif choice == "3":
                    return
            
            # If we reach here, continue to next stage
            break
 
# --- Constants ---
APP_NAME = "AgentLab"
USER_ID = "user_1"
SESSION_ID = "session_1"
 
# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
# --- Custom User Selection Agent ---
class UserSelectionAgent(BaseAgent):
    """
    Custom agent that presents ideas to the user and captures their selection.
    """
    
    # --- Field Declarations for Pydantic ---
    idea_generator: LlmAgent
    validator: LlmAgent
    product_manager: LlmAgent
    prompt_engineer: LlmAgent
    
    # Allow arbitrary types since we're storing agent instances
    model_config = {"arbitrary_types_allowed": True}
 
    def __init__(
        self,
        name: str,
        idea_generator: LlmAgent,
        validator: LlmAgent,
        product_manager: LlmAgent,
        prompt_engineer: LlmAgent,
    ):
        """
        Initialize the UserSelectionAgent with required sub-agents.
        """
        # Define the sub_agents list for the framework
        sub_agents_list = [
            idea_generator,
            validator,
            product_manager,
            prompt_engineer
        ]
        
        # Initialize with Pydantic
        super().__init__(
            name=name,
            idea_generator=idea_generator,
            validator=validator,
            product_manager=product_manager,
            prompt_engineer=prompt_engineer,
            sub_agents=sub_agents_list,
        )
 
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info(f"{self.name} Starting idea generation workflow.")
        
        # 1. Generate ideas
        logger.info(f"{self.name} Running IdeaGenerator...")
        async for event in self.idea_generator.run_async(ctx):
            yield event
            
        # Check if ideas were generated
        if "generated_ideas" not in ctx.session.state:
            logger.error(f"{self.name} Failed to generate ideas. Aborting workflow.")
            return
            
        # 2. Validate ideas
        logger.info(f"{self.name} Running IdeaValidator...")
        async for event in self.validator.run_async(ctx):
            yield event
            
        # Get data from session state
        ideas = ctx.session.state.get("generated_ideas", [])
        validations = ctx.session.state.get("idea_validations", {})
        
        # Ensure validations is a dictionary
        if isinstance(validations, str):
            try:
                import json
                validations = json.loads(validations)
            except json.JSONDecodeError:
                validations = {}
        
        print("\n--- Generated Ideas ---")
        for i, idea in enumerate(ideas, 1):
            print(f"{i}. {idea}")
            if idea in validations:
                print(f"   Validation: {validations[idea]}")
        
        # Get user selection
        try:
            selected_index = int(input("\nSelect an idea to proceed (1-3): "))
            selected_idea = ideas[selected_index - 1]
        except (ValueError, IndexError):
            logger.error("Invalid selection. Using first idea by default.")
            selected_idea = ideas[0]
        
        logger.info(f"{self.name} User selected idea: {selected_idea}")
        ctx.session.state["selected_idea"] = selected_idea
    
        
        # 3. Generate PRD
        logger.info(f"{self.name} Running ProductManager...")
        async for event in self.product_manager.run_async(ctx):
            yield event
            
        # 4. Generate prompts
        logger.info(f"{self.name} Running PromptEngineer...")
        async for event in self.prompt_engineer.run_async(ctx):
            yield event
            
        logger.info(f"{self.name} Workflow completed.")
 
# --- Define the individual LLM agents ---
idea_generator = LlmAgent(
    name="IdeaGenerator",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are an idea generator. Based on the user's input describing what ideas they want,
    generate product ideas as a JSON list. For example, if the user says "AI productivity tools", you might return:
    ["Smart AI calendar assistant", "AI-powered productivity dashboard", "Personal AI task automator"]
    Store the list under key 'generated_ideas'.
    """,
    input_schema=None,
    output_key="generated_ideas",
)

class SerpApiValidator(Agent):
    async def handle(self, conversation, memory):
        ideas = memory["IdeaCoach"]  # list of {"id", "idea"}
        scores = []
        for idea in ideas:
            results = serpapi_search(idea["idea"])
            feasibility = min(len(results)/10, 1.0)
            innovation  = max(1.0 - len(results)/20, 0.0)
            final_score = feasibility * 0.6 + innovation * 0.4
            scores.append({
                "id": idea["id"],
                "feasibility": round(feasibility, 2),
                "innovation": round(innovation, 2),
                "score": round(final_score, 2),
            })
        return scores
 
idea_validator = SerpApiValidator(
    name="IdeaValidator",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are an idea validator. For each idea in 'generated_ideas',
    validate its feasibility, market potential, and innovation score (1-10).
    Return a JSON object where keys are the ideas and values are their scores.
    Example output:
    {
        "Idea 1": {"feasibility": 8, "market": 7, "innovation": 9},
        "Idea 2": {"feasibility": 5, "market": 6, "innovation": 7}
    }
    Store this under key 'idea_validations'.
    """,
    input_schema=None,
    output_key="idea_validations",
)
 
product_manager = LlmAgent(
    name="ProductManager",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are a product manager. Create a Product Requirements Document (PRD)
    for the idea in 'selected_idea'. Include sections for Overview, Features,
    User Stories, and Metrics. Store the PRD under key 'product_prd'.
    """,
    input_schema=None,
    output_key="product_prd",
)
 
prompt_engineer = LlmAgent(
    name="PromptEngineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="""
    You are a prompt engineer. Create 3 effective prompts that could be used
    in LOVABLE and BOLT to create apps based on the 'selected_idea'.
    Store the prompts under key 'app_prompts'.
    """,
    input_schema=None,
    output_key="app_prompts",
)
 
# --- Create the custom agent instance ---
user_selection_agent = UserSelectionAgent(
    name="UserSelectionAgent",
    idea_generator=idea_generator,
    validator=idea_validator,
    product_manager=product_manager,
    prompt_engineer=prompt_engineer,
)
 
# --- Setup Runner and Session ---
session_service = InMemorySessionService()
initial_state = {}  # Start with empty state
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    state=initial_state
)
 
# Create the root agent wrapping our workflow
root_agent = RootAgent(workflow_agent=user_selection_agent)
 
runner = Runner(
    agent=root_agent,  # Now using root_agent instead of user_selection_agent
    app_name=APP_NAME,
    session_service=session_service
)
 
def run_workflow():
    """
    Runs the interactive idea to product workflow.
    """
    # Get initial user prompt
    user_prompt = input("What kind of ideas would you like to generate? (e.g., 'AI productivity tools'): ")
    
    # Run the agent
    content = types.Content(
        role='user',
        parts=[types.Part(text=f"Generate ideas for: {user_prompt}")]
    )
    
    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    )
    
    # Process events
    for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            print("\nFinal Output:", event.content.parts[0].text)
    
    # Display final state
    final_session = session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print("\n--- Final Results ---")
    print("Selected Idea:", final_session.state.get("selected_idea"))
    print("\nPRD:", final_session.state.get("product_prd"))
    print("\nPrompts:", final_session.state.get("app_prompts"))
 
run_workflow()