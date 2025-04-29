from google.adk.agents import LlmAgent
from typing import List, Dict, Optional
import logging
import json

# Configure module-specific logger instead of using basicConfig
logger = logging.getLogger(__name__)
# Only configure if not already configured (prevents duplicate handlers in tests)
if not logger.handlers and not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Mock creativity-prompt library
class CreativityPrompt:
    @staticmethod
    def generate_prompt(problem_statement: str) -> str:
        """Build a hydration-tracking mobile app that:\n"
            "1. Reminds users to drink water based on their personal metrics (weight, age) and activity level.\n"
            "2. Adjusts reminder frequency dynamically using local weather data (e.g. more reminders on hot days).\n"
            "3. Logs each intake and generates weekly hydration reports with motivational tips."""
        return f"""
        Generate 5 innovative ideas to solve the following problem:
        
        PROBLEM: {problem_statement}
        
        For each idea, provide a clear, concise description.
        Format your response as a numbered list with exactly 5 ideas.
        """

def call_llm(prompt: str) -> str:
    """
    Mock function to call an LLM with a prompt.
    In a real implementation, this would call the actual LLM API.
    """
    # This is a mock implementation - in production, this would call the actual LLM
    logger.info(f"Calling LLM with prompt: {prompt}")
    # In a real implementation, this would return the LLM's response
    return "1. Smart notification system that prioritizes alerts based on user behavior patterns.\n2. AI-powered content summarizer for long articles and documents.\n"

def create_idea_coach(model="gemini-2.0-flash"):
    """
    Returns an LLM agent that generates exactly 5 ideas
    for a given problem statement, padding if needed.
    """
    return LlmAgent(
        name="IdeaCoach",
        model=model,
        instruction=(
            "Generate exactly 5 distinct ideas for the given problem statement. "
            "If fewer appear, pad with 'No further idea available'."
        ),
        output_key="ideas"
    )

def parse_ideas(raw_output: str) -> List[str]:
    """
    Parse raw LLM output into a list of idea strings.
    
    Args:
        raw_output: The raw text output from the LLM
        
    Returns:
        List of idea strings
        
    Raises:
        ValueError: If parsing fails
    """
    ideas = []
    try:
        # Split by numbered lines (1., 2., etc.)
        lines = raw_output.strip().split('\n')
        current_idea = ""
        
        for line in lines:
            line = line.strip()
            # Check if this is a new numbered idea
            if line and (line[0].isdigit() and line[1:].startswith('. ')):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = line[line.find(' ')+1:].strip()
            elif line and current_idea:
                # Continue previous idea
                current_idea += " " + line
        
        # Add the last idea if it exists
        if current_idea:
            ideas.append(current_idea)
            
        # Verify we found at least one idea
        if not ideas:
            logger.error("No ideas found in output")
            raise ValueError("No ideas found in output")
            
        logger.info(f"Successfully parsed {len(ideas)} ideas from LLM output")
        return ideas
    except Exception as e:
        logger.error(f"Error parsing ideas: {str(e)}")
        # Don't log the raw output again as it's already logged in generate_ideas
        raise ValueError(f"Failed to parse ideas")

def generate_ideas(problem_statement: str) -> List[Dict]:
    """
    Generate exactly five ideas for the given problem statement.
    
    Args:
        problem_statement: A string describing the problem to solve
        
    Returns:
        A list of dictionaries, each with 'id' and 'idea' keys
        
    Raises:
        ValueError: If problem_statement is empty or less than 10 characters
    """
    # Validate problem statement
    if not problem_statement:
        logger.error("Problem statement is empty")
        raise ValueError("problem too short")
    
    if len(problem_statement.strip()) < 10:
        logger.error(f"Problem statement too short: '{problem_statement}'")
        raise ValueError("problem too short")
    
    # Log the problem statement
    logger.info(f"Generating ideas for problem: {problem_statement}")
    
    # Generate prompt using the creativity library
    prompt = CreativityPrompt.generate_prompt(problem_statement)
    
    # Call LLM with the prompt
    raw_output = call_llm(prompt)
    # Log only the first 100 characters to avoid cluttering logs
    logger.info(f"Raw LLM output: {raw_output[:100]}...")
    
    # Parse the output into ideas
    try:
        parsed_ideas = parse_ideas(raw_output)
        
        # Create the result list with proper format
        result = []
        for i in range(5):
            if i < len(parsed_ideas):
                result.append({"id": i+1, "idea": parsed_ideas[i]})
            else:
                # Pad with default message if fewer than 5 ideas
                result.append({"id": i+1, "idea": "No further idea available"})
                
        logger.info(f"Generated {len(result)} ideas (including {5 - min(len(parsed_ideas), 5)} padding)")
        return result
        
    except ValueError:
        # On parsing failure, wrap the entire raw output as idea #1 and pad
        logger.warning("Returning raw output as idea #1 due to parsing failure")
        
        result = [{"id": 1, "idea": raw_output}]
        # Pad with default message for remaining ideas
        for i in range(2, 6):
            result.append({"id": i, "idea": "No further idea available"})
        
        return result