import os

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

try:
    from crewai_tools import (
        SerperDevTool,
        SerplyNewsSearchTool,
    )
except ImportError:  # pragma: no cover - optional dependency
    SerperDevTool = None
    SerplyNewsSearchTool = None

# Import OpenAI Web Search Tool for market validation
try:
    import sys
    from pathlib import Path
    # Add project root to path for importing services.tools
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from services.tools.openai_web_search import OpenAIWebSearchTool
except ImportError:
    OpenAIWebSearchTool = None


load_dotenv(override=False)

# Prefer an environment override; fall back to a model ID already used elsewhere in this repo.
DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-5-mini")
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "1"))


def _available_tools(*tool_classes):
    """Instantiate available tool classes, ignoring missing optional dependencies."""
    return [tool_cls() for tool_cls in tool_classes if callable(tool_cls)]

@CrewBase
class VenturebotsAiEntrepreneurshipCoachingPlatformCrew:
    """VenturebotsAiEntrepreneurshipCoachingPlatform crew"""

    @agent
    def venturebot_onboarding_agent(self) -> Agent:

        
        return Agent(
            config=self.agents_config["venturebot_onboarding_agent"],
            
            
            tools=_available_tools(),
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=5,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model=DEFAULT_LLM_MODEL,
                temperature=DEFAULT_TEMPERATURE,
            ),
            
        )
    
    @agent
    def venturebot_idea_generator(self) -> Agent:

        
        return Agent(
            config=self.agents_config["venturebot_idea_generator"],
            
            
            tools=_available_tools(SerperDevTool),
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=5,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model=DEFAULT_LLM_MODEL,
                temperature=DEFAULT_TEMPERATURE,
            ),
            
        )
    
    @agent
    def market_validator_agent(self) -> Agent:

        
        return Agent(
            config=self.agents_config["market_validator_agent"],
            
            
            tools=_available_tools(OpenAIWebSearchTool),
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=5,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model=DEFAULT_LLM_MODEL,
                temperature=DEFAULT_TEMPERATURE,
            ),
            
        )
    
    @agent
    def venturebot_product_manager(self) -> Agent:

        
        return Agent(
            config=self.agents_config["venturebot_product_manager"],
            
            
            tools=_available_tools(SerperDevTool),
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=5,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model=DEFAULT_LLM_MODEL,
                temperature=DEFAULT_TEMPERATURE,
            ),
            
        )
    
    @agent
    def venturebot_technical_prompt_engineer(self) -> Agent:

        
        return Agent(
            config=self.agents_config["venturebot_technical_prompt_engineer"],
            
            
            tools=_available_tools(),
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=5,
            max_rpm=None,
            max_execution_time=None,
            llm=LLM(
                model=DEFAULT_LLM_MODEL,
                temperature=DEFAULT_TEMPERATURE,
            ),
            
        )
    

    
    @task
    def venturebot_user_onboarding_and_pain_point_discovery(self) -> Task:
        return Task(
            config=self.tasks_config["venturebot_user_onboarding_and_pain_point_discovery"],
            markdown=False,
            
            
        )
    
    @task
    def venturebot_market_aware_idea_generation(self) -> Task:
        return Task(
            config=self.tasks_config["venturebot_market_aware_idea_generation"],
            markdown=False,
            
            
        )
    
    @task
    def comprehensive_market_validation(self) -> Task:
        return Task(
            config=self.tasks_config["comprehensive_market_validation"],
            markdown=False,
            
            
        )
    
    @task
    def venturebot_product_requirements_and_mvp_development(self) -> Task:
        return Task(
            config=self.tasks_config["venturebot_product_requirements_and_mvp_development"],
            markdown=False,
            
            
        )
    
    @task
    def venturebot_no_code_builder_prompt_generation(self) -> Task:
        return Task(
            config=self.tasks_config["venturebot_no_code_builder_prompt_generation"],
            markdown=False,
            
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the VenturebotsAiEntrepreneurshipCoachingPlatform crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

    def _load_response_format(self, name):
        with open(os.path.join(self.base_directory, "config", f"{name}.json")) as f:
            json_schema = json.loads(f.read())

        return SchemaConverter.build(json_schema)
