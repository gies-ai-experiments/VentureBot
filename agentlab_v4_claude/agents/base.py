from typing import AsyncGenerator
from typing_extensions import override
from pydantic import Field
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

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
            # If this invocation carries the user's reply, capture it
            if hasattr(ctx, 'initial_user_content') and ctx.initial_user_content:
                user_msg = ctx.initial_user_content.parts[0].text
                ctx.session.state[self.memory_key] = user_msg
                yield Event(content={self.memory_key: user_msg})
                # Don't end the invocation here - let the pipeline continue
                ctx.end_invocation = False
                return

            # Otherwise, send the prompt and pause the pipeline
            yield Event(content={"message": self.prompt})
            # Pause the pipeline to wait for user input
            ctx.end_invocation = True

    return InputAgent(name=name, prompt=prompt, memory_key=memory_key) 