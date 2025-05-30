import anthropic
from typing import Dict, Any
# Define web search tool for Claude
web_search_tool = {
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

# Custom function for web search using Claude
def claude_web_search(query: str, anthropic_client: anthropic.Anthropic) -> Dict[str, Any]:
    """
    Use Claude's native web search functionality to search the web
    
    Args:
        query (str): The search query to look up
        
    Returns:
        Dict[str, Any]: Search results with title and content
    """
    try:
        print.info(f"Performing web search for query: {query}")
        # Initial message with the search query
        message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219", 
            max_tokens=4000,
            tools=[web_search_tool],
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
                tool_name = tool_use.name
                tool_params = tool_use.input
                tool_id = tool_use.id
                
                print.debug(f"Tool use detected: {tool_name} with params: {tool_params}")
                
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
                        results.append({"title": f"Result {i+1}", "content": content.text, "position": i+1})
                
                print.info(f"Found {len(results)} search results")
                return {"results": results}
        
        # Handle direct response (no tool use)
        text_content = next((c for c in message.content if getattr(c, 'type', None) == 'text'), None)
        if text_content:
            print.info("Received direct response without tool use")
            return {"results": [{"title": "Direct Response", "content": text_content.text, "position": 1}]}
        
        return {"results": []}
    
    except Exception as e:
        print.error(f"Error in claude_web_search: {str(e)}", exc_info=True)
        return {"results": []}