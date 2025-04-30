import re
import logging
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IdeaCoachAgent:
    """
    Agent that generates creative ideas for a given problem statement.
    
    This is a standalone implementation that doesn't depend on the Google ADK framework.
    """
    
    def __init__(self):
        # Mock creativity prompt templates
        self.creativity_prompts = [
            "Generate 5 distinct innovative ideas for solving: {problem_statement}",
            "Think outside the box and provide 5 unique solutions for: {problem_statement}",
            "Imagine 5 creative approaches to address: {problem_statement}",
            "What are 5 unconventional ways to tackle: {problem_statement}",
            "Provide 5 groundbreaking ideas to resolve: {problem_statement}"
        ]
    
    async def generate_ideas(self, problem_statement: str) -> List[Dict[str, Any]]:
        """
        Generate ideas for a given problem statement.
        
        Args:
            problem_statement: The problem to generate ideas for
            
        Returns:
            A list of dictionaries, each containing an idea and its ID
            
        Raises:
            ValueError: If the problem statement is empty or too short
        """
        # Validate problem statement
        if not problem_statement or len(problem_statement) < 10:
            error_msg = "problem too short"
            logger.error(f"Problem statement validation failed: {error_msg}")
            raise ValueError(error_msg)
        
        # Select a creativity prompt template and format it
        selected_prompt = self.creativity_prompts[0]  # Using the first prompt for simplicity
        prompt = selected_prompt.format(problem_statement=problem_statement)
        
        # Log the prompt
        logger.info(f"Generated prompt: {prompt}")
        
        try:
            # Call the mock LLM function
            raw_output = await self._call_llm(prompt)
            
            # Log the raw LLM output
            logger.info(f"Raw LLM output: {raw_output}")
            
            # Parse the output into ideas
            ideas = self._parse_ideas(raw_output)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Error calling LLM or parsing output: {str(e)}")
            raise
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Mock LLM function that returns a predefined response.
        
        In a real implementation, this would call an actual LLM API.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The raw text output from the LLM
        """
        # Return a mock response with 5 ideas
        return """
        1. Reusable shopping bag made from recycled plastic bottles that folds into a compact pouch
        2. Canvas tote with reinforced handles and a waterproof bottom section
        3. Multi-compartment shopping bag with separate sections for produce, frozen items, and fragile goods
        4. Expandable mesh shopping bag that can adjust to different sizes based on shopping volume
        5. Self-cleaning antimicrobial shopping bag with built-in UV sanitization
        """
    
    def _parse_ideas(self, raw_output: str) -> List[Dict[str, Any]]:
        """
        Parse the raw LLM output into a list of ideas.
        
        Args:
            raw_output: The raw text output from the LLM
            
        Returns:
            A list of dictionaries, each containing an idea and its ID
        """
        ideas = []
        
        try:
            # Try to split by numbered list pattern (e.g., "1.", "2.", etc.)
            parts = re.split(r"\d+\.[\s]*", raw_output)
            # Remove empty parts and the text before the first number if present
            parts = [part.strip() for part in parts if part.strip()]
            
            if not parts:
                # If parsing fails (no separators found), use the entire output as idea #1
                logger.warning("No idea separators found in LLM output, using entire output as idea #1")
                ideas.append({"idea": raw_output.strip(), "id": 1})
            else:
                # Add each parsed idea with an ID
                for i, text in enumerate(parts, 1):
                    if i <= 5:  # Only take up to 5 ideas
                        ideas.append({"idea": text, "id": i})
        except Exception as e:
            # If parsing fails for any reason, use the entire output as idea #1
            logger.error(f"Error parsing ideas: {str(e)}")
            ideas.append({"idea": raw_output.strip(), "id": 1})
        
        # Ensure we have exactly 5 ideas by padding if necessary
        while len(ideas) < 5:
            ideas.append({"idea": "No further idea available", "id": len(ideas) + 1})
        
        return ideas

# For direct execution
if __name__ == "__main__":
    import asyncio
    import json
    
    async def main():
        agent = IdeaCoachAgent()
        try:
            ideas = await agent.generate_ideas("Generate ideas for a reusable shopping bag.")
            print(json.dumps(ideas, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(main())