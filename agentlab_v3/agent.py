# agentlab_v2/agent.py

import yaml
from google.adk.agents import Agent, ParallelAgent, SequentialAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm

from google.adk.tools.function_tool import FunctionTool
from .competitor_search import find_competitors


# No schema classes needed; rely on conversation history for context

# 1) Load your config file
cfg = yaml.safe_load(open("agentlab_v3/config.yaml"))

# 2) Create the leaf Agents
idea_agent = Agent(
    name="IdeaCoach",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction=(
        f"You are an idea coach. Brainstorm {cfg['num_ideas']} distinct ideas based on the user's last message."
    ),
)

validator = Agent(
    name="Validator",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction=(
        "You are an evaluator. Rate the last idea on a scale from 0.0 to 1.0. Reply with only the numeric score."
    ),
)
# Wrap Validator in a ParallelAgent to rate all ideas
validation_agent = ParallelAgent(
    name="ValidateAll",
    sub_agents=[validator],
)

# Prompt engineer agent to produce final self-contained AI prompt
prompt_engineer = Agent(
    name="PromptEngineer",
    model=LiteLlm(model=cfg["model"]),
    instruction="Write a self-contained AI prompt that implements the chosen solution clearly and completely.",
)

# 2) Pick the best idea.
product_manager = Agent(
    name="ProductManager",
    model=LiteLlm(model=cfg["model"]),
    instruction="Select the single most valuable idea from the ideas and scores so far.",
)

    # 3) Turn our competitor finder into a FunctionTool
competitor_tool = FunctionTool(find_competitors)

competitor_agent = Agent(
    name="CompetitorFinder",
    model=LiteLlm(model=cfg["model"]),
    tools=[competitor_tool],
    instruction=(
        "Use the built-in tool `find_competitors(idea)` to look up the top potential competitors "
        "for the chosen product idea. Return a comma-separated list."
    ),
)

# 4) (Optional) Analyze competitors: provide pro and con for each
analysis_agent = Agent(
    name="CompetitorAnalysis",
    model=LiteLlm(model=cfg["model"]),
    instruction=(
        "For each competitor provided in the last user message, and given the selected idea "
        "in the conversation history, provide one pro and one con in bullet points for each competitor."
    ),
)

# 4) Assemble the pipeline
gen_val_sel = SequentialAgent(
    name="GenValidateSelect",
    sub_agents=[idea_agent, validation_agent, product_manager],
)

ensure_quality = LoopAgent(
    name="EnsureQuality",
    sub_agents=[gen_val_sel],
    max_iterations=cfg["max_loops"],
)

# 5) After we’ve looped and chosen the idea, run CompetitorFinder
full_pipeline = SequentialAgent(
    name="FullWorkflow",
    sub_agents=[ensure_quality, competitor_agent, analysis_agent, prompt_engineer],
)

# 7) Expose the root agent for `adk web`
root_agent = full_pipeline

if __name__ == "__main__":  # Interactive CLI workflow
    import uuid
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
    from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
    from google.genai.types import UserContent

    # Initialize in-memory services and session/user identifiers
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    memory_service = InMemoryMemoryService()
    user_id = "user"
    session_id = str(uuid.uuid4())

    print("Welcome to AgentLab V3 Interactive Workflow")

    # Stage 1: Brainstorm ideas
    input("\n=== Stage 1: Idea Brainstorm ===\nPress Enter to begin...")
    prompt = input("Enter your prompt/context: ")
    runner = Runner(
        app_name="agentlab_v3",
        agent=idea_agent,
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service,
    )
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=UserContent(prompt),
    ):
        if event.author == idea_agent.name:
            ideas = event.content.text or ""
            print(f"\nIdeas:\n{ideas}")

    # Stage 2: Validation
    input("\nPress Enter to proceed to validation stage...")
    runner.agent = validation_agent
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=UserContent(""),
    ):
        if event.author == validator.name:
            scores = event.content.text or ""
            print(f"\nScores:\n{scores}")

    # Stage 3: User selects idea
    input("\nPress Enter to proceed to selecting your idea...")
    print(f"\nIdeas:\n{ideas}")
    print(f"\nScores:\n{scores}")
    selected_idea = input("Enter the idea you want to proceed with: ")
    print(f"\nProceeding with selected idea:\n{selected_idea}")

    # Stage 4: Competitor search
    input("\nPress Enter to find competitors...")
    runner.agent = competitor_agent
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=UserContent(selected_idea),
    ):
        if event.author == competitor_agent.name:
            competitors = event.content.text or ""
            print(f"\nCompetitors:\n{competitors}")

    # Stage 5: Competitor analysis pros and cons
    input("\nPress Enter to analyze competitors and generate pros/cons...")
    runner.agent = analysis_agent
    analysis_input = f"Idea: {selected_idea}\nCompetitors: {competitors}"
    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=UserContent(analysis_input),
    ):
        if event.author == analysis_agent.name:
            pros_cons = event.content.text or ""
            print(f"\nPros and Cons:\n{pros_cons}")
    print("\nWorkflow complete.")