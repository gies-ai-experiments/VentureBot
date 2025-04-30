from google.adk.agents import BaseAgent, LlmAgent
import aiohttp
import asyncio
import logging
import math
import time
import random
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import PrivateAttr
from google.adk.events import Event, EventActions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    """
    Agent that scores ideas based on impact, feasibility, and innovation.
    
    Integrates with Google ADK framework and provides methods to score ideas
    using search API data and LLM-based ratings.
    """
    
    _llm: LlmAgent = PrivateAttr()
    _search_api_key: str = PrivateAttr()
    _search_endpoint: str = PrivateAttr()
    
    def __init__(self, name="ValidationAgent", model="gemini-2.0-flash", 
                 search_api_key: str = "", search_endpoint: str = ""):
        """
        Initialize the ValidationAgent with search API credentials.
        
        Args:
            name: Name of the agent
            model: LLM model to use
            search_api_key: API key for the search service
            search_endpoint: Endpoint URL for the search service
        """
        # Initialize LLM agent with rating instruction
        llm = LlmAgent(name=f"{name}_LLM", model=model,
                      instruction="Rate the following idea on a scale of 0-10 for {criterion}: {idea}")
        
        super().__init__(name=name, sub_agents=[llm])
        self._llm = llm
        self._search_api_key = search_api_key
        self._search_endpoint = search_endpoint
        logger.info(f"ValidationAgent initialized with search endpoint: {search_endpoint}")
    
    async def run_async(self, *, user_id: str, session_id: str, new_message: List[Dict], 
                      run_config=None) -> AsyncGenerator[Event, None]:
        """
        Process a list of ideas and score them.
        This method adapts the Google ADK framework to our requirements.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            new_message: List of idea dictionaries to score
            run_config: Optional configuration
            
        Yields:
            Events containing the scored ideas or error messages
        """
        try:
            # Validate that new_message is a list of ideas
            if not isinstance(new_message, list):
                raise ValueError("Input must be a list of ideas")
                
            # Score the ideas
            start_time = time.time()
            scored_ideas = await self.score_ideas(new_message)
            total_time = time.time() - start_time
            
            logger.info(f"Scored {len(scored_ideas)} ideas in {total_time:.2f} seconds")
            
            # Yield the scored ideas as an event
            yield Event.message({"scored_ideas": scored_ideas})
            
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error: {str(e)}")
            yield Event.message({"error": str(e)})
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error in run_async: {str(e)}")
            yield Event.message({"error": f"Failed to score ideas: {str(e)}"})
    
    async def score_ideas(self, ideas: List[Dict]) -> List[Dict]:
        """
        Score a list of ideas based on impact, feasibility, and innovation.
        
        Args:
            ideas: List of idea dictionaries, each with "idea" and "id" keys
            
        Returns:
            List of dictionaries with scores for each idea
            
        Raises:
            ValueError: If the ideas list is empty
        """
        # Validate input
        if not ideas:
            logger.error("No ideas to validate")
            raise ValueError("no ideas to validate")
            
        logger.info(f"Scoring {len(ideas)} ideas")
        
        # Track errors for partial results
        errors = []
        scored_ideas = []
        
        # Process each idea
        for idea in ideas:
            try:
                # Validate idea format
                if "idea" not in idea or "id" not in idea:
                    logger.warning(f"Skipping idea missing required fields: {idea}")
                    continue
                
                idea_text = idea["idea"]
                idea_id = idea["id"]
                
                logger.info(f"Scoring idea {idea_id}: {idea_text[:50]}...")
                
                # Calculate scores
                start_time = time.time()
                
                # Get impact score from search API
                try:
                    impact_score = await self._popularity_score(idea_text)
                    # Scale from [0,1] to [0,10]
                    impact_score = self._clamp(impact_score * 10, 0, 10)
                except Exception as e:
                    logger.error(f"Error calculating impact score for idea {idea_id}: {str(e)}")
                    impact_score = 0.0
                
                # Get feasibility score
                try:
                    feasibility_score = await self._rate_text(idea_text, "feasibility")
                except Exception as e:
                    logger.error(f"Error calculating feasibility score for idea {idea_id}: {str(e)}")
                    feasibility_score = 0
                
                # Get innovation score
                try:
                    innovation_score = await self._rate_text(idea_text, "innovation")
                except Exception as e:
                    logger.error(f"Error calculating innovation score for idea {idea_id}: {str(e)}")
                    innovation_score = 0
                
                processing_time = time.time() - start_time
                logger.info(f"Scored idea {idea_id} in {processing_time:.2f} seconds")
                
                # Add scored idea to results
                scored_ideas.append({
                    "id": idea_id,
                    "impact": int(impact_score),
                    "feasibility": feasibility_score,
                    "innovation": innovation_score
                })
                
            except Exception as e:
                logger.error(f"Unexpected error processing idea {idea.get('id', 'unknown')}: {str(e)}")
                errors.append(str(e))
        
        # If there were errors, include them in the result
        result = scored_ideas
        if errors:
            logger.warning(f"Completed with {len(errors)} errors")
            result = {"scored_ideas": scored_ideas, "errors": errors}
        
        return result
    
    async def _popularity_score(self, query: str) -> float:
        """
        Calculate a popularity score for a query using a search API.
        
        Args:
            query: The search query (idea text)
            
        Returns:
            Normalized score between 0.0 and 1.0
        """
        start_time = time.time()
        
        try:
            # Prepare search API request
            params = {
                "q": query,
                "api_key": self._search_api_key
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.get(self._search_endpoint, params=params, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Search API error: {response.status} - {await response.text()}")
                        return 0.0
                    
                    data = await response.json()
                    
                    # Extract total hits (this would depend on the actual API response format)
                    # For example, with Bing or SerpAPI it might be something like:
                    total_hits = data.get("total_results", 0)
                    
                    # For mock implementation, if no real API is available:
                    if not self._search_api_key or not self._search_endpoint:
                        # Generate a random number of hits for testing
                        total_hits = random.randint(100, 1000000)
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Log hits and latency
            logger.info(f"Search query '{query[:30]}...' returned {total_hits} hits in {latency:.2f} seconds")
            
            # Normalize hits using log1p (log(1+x)) and cap at 1.0
            # This gives a score between 0 and 1, with diminishing returns for very high hit counts
            normalized_score = min(math.log1p(total_hits) / 15, 1.0)  # Dividing by 15 to normalize, adjust as needed
            
            return normalized_score
            
        except asyncio.TimeoutError:
            logger.error(f"Search API timeout for query: {query[:30]}...")
            return 0.0
        except Exception as e:
            logger.error(f"Error in _popularity_score: {str(e)}")
            return 0.0
    
    async def _rate_text(self, text: str, criterion: str) -> int:
        """
        Rate text on a specific criterion using an LLM.
        
        Args:
            text: The text to rate (idea)
            criterion: The criterion to rate on (e.g., "feasibility", "innovation")
            
        Returns:
            Integer score between 0 and 10
        """
        try:
            # For a real implementation with LLM:
            if self._llm:
                # Format the prompt with the criterion and idea
                prompt = f"Rate the following idea on a scale of 0-10 for {criterion}: {text}"
                
                # Update the LLM instruction
                self._llm.instruction = prompt
                
                # Call the LLM
                responses = self._llm.run_async(
                    user_id="system",
                    session_id="validation",
                    new_message=prompt
                )
                
                # Collect response from the LLM
                raw_output = ""
                async for event in responses:
                    if hasattr(event, 'content') and event.content:
                        raw_output += event.content
                    elif isinstance(event, dict) and 'result' in event:
                        raw_output += event['result']
                    elif isinstance(event, dict) and 'content' in event:
                        raw_output += event['content']
                
                # Extract the numeric score from the response
                # This is a simple implementation - in practice, you'd want more robust parsing
                for word in raw_output.split():
                    if word.isdigit() and 0 <= int(word) <= 10:
                        return int(word)
                
                # If no valid score found, default to a mock score
                logger.warning(f"Could not extract valid score from LLM response for {criterion}")
            
            # Mock implementation for testing or if LLM fails
            if criterion == "feasibility":
                # Feasibility tends to be higher for simpler ideas
                return random.randint(5, 9)
            elif criterion == "innovation":
                # Innovation can vary widely
                return random.randint(3, 10)
            else:
                return random.randint(0, 10)
                
        except Exception as e:
            logger.error(f"Error in _rate_text for {criterion}: {str(e)}")
            return 0
    
    def _clamp(self, value: float, min_value: float, max_value: float) -> float:
        """
        Clamp a value between a minimum and maximum.
        
        Args:
            value: The value to clamp
            min_value: The minimum allowed value
            max_value: The maximum allowed value
            
        Returns:
            The clamped value
        """
        return max(min_value, min(value, max_value))

# For direct execution and testing
if __name__ == "__main__":
    import asyncio
    import json
    
    async def test():
        # Create a validation agent with mock search API credentials
        agent = ValidationAgent(search_api_key="nwTUxMTTFaZGcpPsa3P3wakm", search_endpoint="https://www.searchapi.io/api/v1/search")
        
        # Test ideas
        test_ideas = [
            {"id": 1, "idea": "Reusable shopping bag made from recycled plastic bottles"},
            {"id": 2, "idea": "Canvas tote with reinforced handles and a waterproof bottom"},
            {"id": 3, "idea": "Multi-compartment shopping bag with separate sections for different items"},
            {"id": 4, "idea": "Expandable mesh shopping bag that adjusts to different sizes"},
            {"id": 5, "idea": "Self-cleaning antimicrobial shopping bag with UV sanitization"}
        ]
        
        try:
            # Score the ideas
            scored_ideas = await agent.score_ideas(test_ideas)
            print("\n=== Scored Ideas ===")
            print(json.dumps(scored_ideas, indent=2))
            
            # Test with empty list
            try:
                await agent.score_ideas([])
            except ValueError as e:
                print(f"\n=== Expected ValueError: {str(e)} ===")
            
            # Test with invalid idea (missing fields)
            partial_results = await agent.score_ideas([{"id": 6}])
            print("\n=== Partial Results (with invalid idea) ===")
            print(json.dumps(partial_results, indent=2))
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(test())