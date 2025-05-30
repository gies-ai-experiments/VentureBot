# Google Agent Developer Kit (ADK) Documentation

This document provides an overview of the Google Agent Developer Kit (ADK) as referenced in our AgentLab project.

## What is Google ADK?

The Agent Development Kit (ADK) is a flexible and modular framework for developing and deploying AI agents. While optimized for Gemini and the Google ecosystem, ADK is model-agnostic and deployment-agnostic, making it compatible with various frameworks. ADK was designed to make agent development feel more like software development, simplifying the creation, deployment, and orchestration of agent architectures ranging from simple tasks to complex workflows.

## Key Features

- **Multi-agent by design**: Compose agents in parallel, sequential, or hierarchical workflows
- **Model-agnostic**: Works with Gemini, GPT-4o, Claude, Mistral, and others via LiteLlm
- **Modular and scalable**: Define specialized agents and delegate intelligently using built-in orchestration
- **Streaming-ready**: Supports real-time interaction, including bidirectional audio/video
- **Built-in tooling**: Includes local CLI and web UI for debugging and evaluation

## Agent Types in ADK

ADK provides different agent categories to meet various requirements:

1. **LLM Agents** (`LlmAgent`, `Agent`): Utilize Large Language Models to understand natural language, reason, plan, generate responses, and decide which tools to use.

2. **Workflow Agents**: Orchestrate complex interactions between agents:
   - `SequentialAgent`: Runs sub-agents in a predefined sequence
   - `ParallelAgent`: Runs sub-agents concurrently
   - `LoopAgent`: Repeatedly runs sub-agents until a condition is met

3. **Custom Agents**: Extend `BaseAgent` for specialized capabilities or unique integrations.

## Installation

Install the latest stable release using pip:

```bash
pip install google-adk
```

For the development version with latest features:

```bash
pip install git+https://github.com/google/adk-python.git@main
```

## Running ADK Applications

ADK provides multiple ways to interact with your agents:

- **Dev UI**: `adk web` - Interactive browser interface
- **Terminal**: `adk run` - Command-line interface
- **API Server**: `adk api_server` - Local FastAPI server

## Basic Example

Here's a simple example of creating an agent with ADK:

```python
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Create a simple agent
agent = Agent(
    name="SimpleAssistant",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction="You are a helpful assistant that answers questions clearly and concisely."
)

# Expose the agent as the root agent
root_agent = agent
```

## Multi-Agent Example (like in AgentLab)

```python
from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
import yaml

# Load configuration
cfg = yaml.safe_load(open("config.yaml"))

# Create individual agents
idea_agent = Agent(
    name="IdeaGenerator",
    model=LiteLlm(model=cfg["model"]),
    instruction=f"Brainstorm {cfg['num_ideas']} ideas based on the user's request."
)

validator = Agent(
    name="Validator",
    model=LiteLlm(model=cfg["model"]),
    instruction="Evaluate each idea on a scale from 0.0 to 1.0."
)

# Create a parallel validation agent
validation_agent = ParallelAgent(
    name="ValidateAll",
    sub_agents=[validator]
)

# Chain agents sequentially
pipeline = SequentialAgent(
    name="MainWorkflow",
    sub_agents=[idea_agent, validation_agent]
)

# Add iteration with LoopAgent
iterative_pipeline = LoopAgent(
    name="IterativeWorkflow",
    sub_agents=[pipeline],
    max_iterations=cfg["max_loops"]
)

# Set the root agent
root_agent = iterative_pipeline
```

## Function Tools

ADK allows you to create tools by wrapping Python functions:

```python
from google.adk.tools.function_tool import FunctionTool

def search_function(query: str) -> list:
    """Search for information using the given query."""
    # Implementation here
    return results

search_tool = FunctionTool(search_function)

tool_enabled_agent = Agent(
    name="SearchAgent",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    tools=[search_tool],
    instruction="Use the search tool to find information when needed."
)
```

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [GitHub Repository](https://github.com/google/adk-python)
- [Sample Agents](https://github.com/google/adk-samples)
- [Tutorials](https://google.github.io/adk-docs/tutorials/)

## License

ADK is licensed under the Apache 2.0 License.