# idea_coach_adk.py
# Install Google ADK to run this module:
#     pip install google-adk

import logging
import re
from google_adk.agents import LlmAgent, BaseAgent, SequentialAgent
from google_adk.runtime.session import Session
from google_adk.agents.invocation_context import InvocationContext
from google_adk.events import Event

# Configure module-specific logger
logger = logging.getLogger(__name__)
if not logger.handlers and not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ParseIdeasAgent(BaseAgent):
    """
    Parses raw LLM output into exactly five ideas, padding if necessary.
    """
    def __init__(self, raw_key: str = "raw_output", ideas_key: str = "ideas", max_ideas: int = 5):
        super().__init__(name="ParseIdeas")
        self.raw_key = raw_key
        self.ideas_key = ideas_key
        self.max_ideas = max_ideas

    async def _run_async_impl(self, ctx: InvocationContext):
        raw_text = ctx.session.state.get(self.raw_key, "")
        # Split on numbered list markers
        parts = re.split(r"\n\s*\d+\.\s*", raw_text)
        ideas = [p.strip().rstrip('.') for p in parts if p.strip()]
        # Pad list to max_ideas
        while len(ideas) < self.max_ideas:
            ideas.append("No further idea available")
        ctx.session.state[self.ideas_key] = ideas[: self.max_ideas]
        logger.info(f"Parsed {len(ctx.session.state[self.ideas_key])} ideas into state['{self.ideas_key}']")
        yield Event(author=self.name)


# LLM Agent that generates ideas
idea_generator = LlmAgent(
    name="IdeaGenerator",
    model="claude-3-7-sonnet-20250219",
    instruction=(
        "You are an idea coach. Given the problem statement stored in state['problem_statement'], "
        "generate exactly five distinct ideas numbered '1.'–'5.'. "
        "If fewer than five appear, pad with 'No further idea available'."
    ),
    output_key="raw_output"
)

# Orchestrator: generate then parse
root_agent = SequentialAgent(
    name="IdeaCoachAgent",
    sub_agents=[idea_generator, ParseIdeasAgent()]
)


def run_idea_coach(problem_statement: str) -> list[str]:
    """
    Synchronously run the IdeaCoach multi-agent pipeline.

    Args:
        problem_statement: The text describing the problem (min. 10 chars).
    Returns:
        List of five idea strings.

    Raises:
        ValueError: If problem_statement is too short.
    """
    if not problem_statement or len(problem_statement.strip()) < 10:
        logger.error(f"Problem statement too short: '{problem_statement}'")
        raise ValueError("problem too short")

    logger.info(f"Starting idea generation for: {problem_statement}")
    session = Session()
    session.state['problem_statement'] = problem_statement
    root_agent.run(session=session)
    ideas = session.state.get('ideas', [])
    logger.info(f"Completed idea generation: {ideas}")
    return ideas