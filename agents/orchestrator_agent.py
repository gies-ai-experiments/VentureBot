from google.adk.agents import BaseAgent
from idea_coach_agent import IdeaCoachAgent
from validation_agent import ValidationAgent
from product_manager_agent import ProductManagerAgent
#from prompt_engineering_agent import PromptEngineeringAgent
#from pitch_coach_agent import PitchCoachAgent

class OrchestratorAgent(BaseAgent):
    """
    Agent that orchestrates the workflow between specialist agents.
    
    This agent coordinates the execution of specialist agents to complete
    a multi-step workflow for idea generation, validation, and product development.
    """
    
    def __init__(self, name="Orchestrator", sub_agents=None):
        """
        Initialize the OrchestratorAgent with specialist sub-agents.
        
        Args:
            name: Name of the agent
            sub_agents: List of specialist agents to orchestrate
        """
        super().__init__(name=name, sub_agents=sub_agents or [])

# instantiate your specialist agents
idea_coach = IdeaCoachAgent(name="IdeaCoach")
validation = ValidationAgent(name="ValidationAgent", search_api_key="nwTUxMTTFaZGcpPsa3P3wakm", search_endpoint="https://www.searchapi.io/api/v1/search")
product_manager = ProductManagerAgent(name="ProductManager")
#prompt_engineer = PromptEngineeringAgent(name="PromptEngineer")
#pitch_coach = PitchCoachAgent(name="PitchCoach")

# create orchestrator and assign sub_agents
orchestrator = OrchestratorAgent(
    name="Orchestrator",
    sub_agents=[
        idea_coach,
        validation,
        product_manager,
        #prompt_engineer,
        #pitch_coach
    ]
)

# Add main execution code if needed
if __name__ == "__main__":
    print(f"Orchestrator initialized with {len(orchestrator.sub_agents)} specialist agents")
    # Add code to run the orchestrator