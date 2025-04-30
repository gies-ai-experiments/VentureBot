from orchestrator_agent import OrchestratorAgent
from idea_coach_agent import IdeaCoachAgent
from validation_agent import ValidationAgent
from product_manager_agent import ProductManagerAgent
from prompt_engineering_agent import PromptEngineeringAgent
from pitch_coach_agent import PitchCoachAgent

# instantiate your specialist agents
idea_coach       = IdeaCoachAgent(name="IdeaCoach")
validation      = ValidationAgent(name="ValidationAgent", search_api_key="YOUR_KEY", search_endpoint="YOUR_ENDPOINT")
product_manager = ProductManagerAgent(name="ProductManager")
prompt_engineer = PromptEngineeringAgent(name="PromptEngineer")
pitch_coach     = PitchCoachAgent(name="PitchCoach")

# create orchestrator and assign sub_agents
orchestrator = OrchestratorAgent(
    name="Orchestrator",
    sub_agents=[
        idea_coach,
        validation,
        product_manager,
        prompt_engineer,
        pitch_coach
    ]
)