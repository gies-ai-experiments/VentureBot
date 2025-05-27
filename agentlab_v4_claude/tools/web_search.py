import logging
from typing import Dict, Any, List
import anthropic
from ..utils.config import get_anthropic_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=get_anthropic_api_key())

# Define web search tool schema
WEB_SEARCH_TOOL = {
    "name": "search_internet",
    "description": "Search the internet for latest information on a topic",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on the internet",
            }
        },
        "required": ["query"],
    }
}

def claude_web_search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Use Claude's native web search functionality to search the web.
    
    Args:
        query (str): The search query to look up
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary containing search results
    """
    try:
        # Initial message with the search query
        message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219", 
            max_tokens=4000,
            tools=[WEB_SEARCH_TOOL],
            messages=[
                {
                    "role": "user",
                    "content": f"Search the web for information about: {query}"
                }
            ]
        )
        
        # Handle tool use if Claude decides to use the search tool
        if hasattr(message, 'stop_reason') and message.stop_reason == "tool_use":
            tool_use = next((c for c in message.content if getattr(c, 'type', None) == 'tool_use'), None)
            if tool_use:
                return _handle_tool_use(query, tool_use)
        
        # Handle direct response (no tool use)
        return _handle_direct_response(message)
    
    except Exception as e:
        logger.error(f"Error in claude_web_search: {str(e)}")
        return {"results": []}

def _handle_tool_use(query: str, tool_use: Any) -> Dict[str, List[Dict[str, Any]]]:
    """Handle tool use response from Claude."""
    tool_name = tool_use.name
    tool_params = tool_use.input
    tool_id = tool_use.id
    
    # Continue the conversation to get search results
    search_response = anthropic_client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=5000,
        messages=[
            {
                "role": "user",
                "content": f"Search the web for information about: {query}"
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "I'll search the web for information on this topic."
                    },
                    {
                        "type": "tool_use",
                        "name": tool_name,
                        "id": tool_id,
                        "input": tool_params
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "result": f"Please provide search results for: {query}"
                    }
                ]
            }
        ]
    )
    
    # Extract text content from the response
    results = []
    for i, content in enumerate(search_response.content):
        if getattr(content, 'type', None) == "text":
            results.append({
                "title": f"Result {i+1}",
                "content": content.text,
                "position": i+1
            })
    
    return {"results": results}

def _handle_direct_response(message: Any) -> Dict[str, List[Dict[str, Any]]]:
    """Handle direct response from Claude (no tool use)."""
    text_content = next((c for c in message.content if getattr(c, 'type', None) == 'text'), None)
    if text_content:
        return {
            "results": [{
                "title": "Direct Response",
                "content": text_content.text,
                "position": 1
            }]
        }
    return {"results": []} 