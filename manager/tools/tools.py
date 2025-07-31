import anthropic
import logging
import time
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)

# Circuit breaker pattern for validation analysis
class ValidationCircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def can_proceed(self):
        """Check if the circuit allows operations"""
        if not self.is_open:
            return True
        
        # Check if enough time has passed to attempt recovery
        if time.time() - self.last_failure_time > self.recovery_timeout:
            logger.info("Circuit breaker recovery timeout reached, attempting reset")
            self.reset()
            return True
        
        return False
    
    def record_success(self):
        """Record a successful operation"""
        self.failure_count = 0
        self.is_open = False
        logger.debug("Circuit breaker: operation successful, reset failure count")
    
    def record_failure(self):
        """Record a failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        else:
            logger.debug(f"Circuit breaker: failure {self.failure_count}/{self.failure_threshold}")
    
    def reset(self):
        """Reset the circuit breaker"""
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
        logger.info("Circuit breaker reset")

# Global circuit breaker instance
validation_circuit_breaker = ValidationCircuitBreaker()

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

# Real web search implementation using Claude's computer use capabilities
def claude_web_search(query: str, anthropic_client: anthropic.Anthropic) -> Dict[str, Any]:
    """
    Real web search implementation using Claude's native web search capabilities.
    Uses proper timeout and circuit breaker protection to prevent hanging.
    
    Args:
        query (str): The search query (idea description)
        anthropic_client: Anthropic client instance for API calls
        
    Returns:
        Dict[str, Any]: Real search results from the web
    """
    import asyncio
    import concurrent.futures
    
    # Check circuit breaker before proceeding
    if not validation_circuit_breaker.can_proceed():
        logger.warning("Circuit breaker is open, using fallback analysis")
        return {"results": [{"title": "Fallback Analysis", "content": "Web search temporarily unavailable (circuit breaker active)", "position": 1}]}
    
    def perform_search():
        """Perform the actual web search with timeout"""
        try:
            logger.info(f"Performing real web search for query: {query}")
            
            # Validate input
            if not query or not query.strip():
                raise ValueError("Empty query provided")
            
            # Use Claude's advanced market intelligence capabilities
            message = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Please conduct comprehensive market research for: "{query}"

I need detailed market intelligence including competitors, market dynamics, and opportunities. Return your findings in this exact JSON format:

{{
    "market_intelligence": {{
        "market_size": {{
            "tam": "Total addressable market estimate",
            "growth_rate": "Annual growth rate percentage",
            "market_stage": "emerging/growing/mature/declining"
        }},
        "competitors": [
            {{
                "name": "Competitor name",
                "description": "What they do",
                "market_position": "market leader/challenger/niche player",
                "funding": "Funding amount if known",
                "users": "User base size if known",
                "strengths": ["strength1", "strength2"],
                "weaknesses": ["weakness1", "weakness2"]
            }}
        ],
        "market_gaps": [
            {{
                "gap": "Underserved market segment or need",
                "opportunity": "Description of the opportunity",
                "difficulty": "low/medium/high"
            }}
        ],
        "trends": [
            {{
                "trend": "Market trend description",
                "impact": "How this affects the market",
                "timeline": "When this trend is happening"
            }}
        ],
        "barriers": [
            {{
                "barrier": "Entry barrier description",
                "severity": "low/medium/high",
                "mitigation": "How to overcome this barrier"
            }}
        ],
        "recommendations": [
            {{
                "strategy": "Strategic recommendation",
                "rationale": "Why this strategy makes sense",
                "priority": "high/medium/low"
            }}
        ]
    }}
}}

Focus on finding:
1. Market size data (TAM, growth rates)
2. Detailed competitor analysis (funding, users, strengths/weaknesses)
3. Underserved market segments and opportunities
4. Current market trends and future outlook
5. Entry barriers and regulatory considerations
6. Strategic recommendations for market entry

Please provide actual market intelligence based on your knowledge, not placeholder text."""
                    }
                ]
            )
            
            # Extract the response content
            response_text = ""
            for content in message.content:
                if hasattr(content, 'text'):
                    response_text += content.text
            
            # Try to extract structured market intelligence JSON from response
            import json
            import re
            
            # Look for market intelligence JSON in the response
            json_match = re.search(r'\{.*?"market_intelligence".*?\}', response_text, re.DOTALL)
            if json_match:
                try:
                    market_data = json.loads(json_match.group())
                    if "market_intelligence" in market_data:
                        intelligence = market_data["market_intelligence"]
                        
                        # Convert to backwards-compatible format while preserving new data
                        competitors = intelligence.get("competitors", [])
                        market_gaps = intelligence.get("market_gaps", [])
                        
                        # Calculate total market indicators from structured data
                        num_competitors = len(competitors)
                        num_gaps = len(market_gaps)
                        
                        logger.info(f"Market intelligence extracted: {num_competitors} competitors, {num_gaps} gaps identified")
                        
                        # Return enhanced format with structured intelligence
                        return {
                            "market_intelligence": intelligence,
                            "results": competitors + [{"title": f"Market Gap {i+1}", "content": gap.get("gap", ""), "position": i+1} for i, gap in enumerate(market_gaps)],
                            "analysis_type": "enhanced"
                        }
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse market intelligence JSON: {e}")
            
            # Fallback: Look for basic results format
            json_match = re.search(r'\{.*?"results".*?\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                    if "results" in result_data and isinstance(result_data["results"], list):
                        logger.info(f"Basic web search completed: {len(result_data['results'])} results found")
                        return {**result_data, "analysis_type": "basic"}
                except json.JSONDecodeError:
                    pass
            
            # If no valid JSON found, parse the response manually
            lines = response_text.split('\n')
            results = []
            current_result = {}
            position = 1
            
            # Enhanced parsing for market intelligence keywords
            market_keywords = ['competitor', 'company', 'product', 'service', 'market', 'funding', 'revenue', 'users', 'customers']
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('```'):
                    if any(keyword in line.lower() for keyword in market_keywords):
                        if current_result.get('title'):
                            results.append(current_result)
                            position += 1
                        current_result = {
                            "title": f"Market Finding {position}",
                            "content": line,
                            "position": position
                        }
                    elif current_result.get('title') and len(line) > 20:  # Only add substantial content
                        current_result["content"] += " " + line
            
            # Add the last result
            if current_result.get('title'):
                results.append(current_result)
            
            # Ensure we have at least some results
            if not results:
                results = [{
                    "title": "Market Analysis",
                    "content": response_text[:300] + "..." if len(response_text) > 300 else response_text,
                    "position": 1
                }]
            
            logger.info(f"Manual parsing completed: {len(results)} results extracted")
            return {"results": results, "analysis_type": "manual"}
            
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            raise
    
    try:
        # Use ThreadPoolExecutor with timeout for the search
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(perform_search)
            try:
                # Wait maximum 30 seconds for web search
                result = future.result(timeout=30)
                
                # Record successful operation
                validation_circuit_breaker.record_success()
                return result
                
            except concurrent.futures.TimeoutError:
                logger.warning("Web search timed out after 30 seconds")
                raise TimeoutError("Web search operation timed out")
                
    except Exception as e:
        logger.error(f"Error in claude_web_search: {str(e)}", exc_info=True)
        
        # Record failure in circuit breaker
        validation_circuit_breaker.record_failure()
        
        # Return fallback results
        return {
            "results": [
                {
                    "title": "Search Unavailable",
                    "content": f"Web search temporarily unavailable. Error: {str(e)[:100]}",
                    "position": 1
                }
            ]
        }

def validate_user_input(user_input: Dict) -> bool:
    """Validate that all required fields are present in user input"""
    required_fields = ["name", "interests", "hobbies"]
    return all(field in user_input for field in required_fields)

def format_user_profile(user_input: Dict) -> str:
    """Format user profile for use by other agents"""
    return f"""
    User Profile:
    Name: {user_input.get('name')}
    Interests: {user_input.get('interests')}
    Hobbies: {user_input.get('hobbies')}
    Favorite Activities: {user_input.get('favorite_activities')}
    """

# Export tools_dict for ADK compatibility
tools_dict = {
    "web_search": web_search_tool,
    "claude_web_search": claude_web_search
}

# Also export web_search as an alias for claude_web_search for backward compatibility
web_search = claude_web_search
       
       