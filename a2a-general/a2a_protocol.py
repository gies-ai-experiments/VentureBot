import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from ...tools.tools import claude_web_search

class AgentRequest(BaseModel):
    " Stantard request format for agents in the A2A protocol. "
    ...

class AgentResponse(BaseModel):
    " Standard response format for agents in the A2A protocol. "
    ...

