"""
OpenAI Web Search Tool for VentureBots Market Validation.

This module provides a CrewAI-compatible tool that uses OpenAI's Responses API
with the built-in web_search capability for real-time market research.
"""

import os
import json
from typing import Optional, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class OpenAIWebSearchInput(BaseModel):
    """Input schema for OpenAI Web Search tool."""
    query: str = Field(
        ...,
        description="The search query for market research, competitive analysis, or industry trends"
    )


class OpenAIWebSearchTool(BaseTool):
    """
    A CrewAI tool that uses OpenAI's Responses API with web search capability.
    
    This tool enables agents to perform real-time web searches for:
    - Competitive landscape analysis
    - Market size and trends research
    - Industry news and developments
    - Customer demand indicators
    """
    
    name: str = "openai_web_search"
    description: str = (
        "Search the web for real-time market research, competitive analysis, "
        "industry trends, and business intelligence using OpenAI's web search. "
        "Use this for current market data, competitor information, and trend analysis."
    )
    args_schema: Type[BaseModel] = OpenAIWebSearchInput
    
    model: str = Field(default="gpt-4o")
    reasoning_effort: str = Field(default="low")
    
    def _run(self, query: str) -> str:
        """
        Execute a web search using OpenAI's Responses API.
        
        Args:
            query: The search query for market research
            
        Returns:
            A formatted string containing the search results and analysis
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OPENAI_API_KEY environment variable not set"
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": self.model,
                    "reasoning": {"effort": self.reasoning_effort},
                    "tools": [
                        {
                            "type": "web_search"
                        }
                    ],
                    "tool_choice": "auto",
                    "include": ["web_search_call.action.sources"],
                    "input": query
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return f"Error: OpenAI API returned status {response.status_code}: {response.text}"
            
            result = response.json()
            return self._format_response(result)
            
        except requests.exceptions.Timeout:
            return "Error: Request to OpenAI API timed out"
        except requests.exceptions.RequestException as e:
            return f"Error: Failed to connect to OpenAI API: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Failed to parse OpenAI API response"
    
    def _format_response(self, result: dict) -> str:
        """Format the API response into a readable string."""
        output_parts = []
        
        # Extract the main output
        if "output" in result:
            for item in result.get("output", []):
                if item.get("type") == "message":
                    content = item.get("content", [])
                    for c in content:
                        if c.get("type") == "output_text":
                            output_parts.append(c.get("text", ""))
                
                # Include web search sources if available
                if item.get("type") == "web_search_call":
                    action = item.get("action", {})
                    sources = action.get("sources", [])
                    if sources:
                        output_parts.append("\n\n**Sources:**")
                        for source in sources[:5]:  # Limit to top 5 sources
                            title = source.get("title", "Unknown")
                            url = source.get("url", "")
                            output_parts.append(f"- [{title}]({url})")
        
        if not output_parts:
            # Fallback: return raw response for debugging
            return json.dumps(result, indent=2)
        
        return "\n".join(output_parts)
