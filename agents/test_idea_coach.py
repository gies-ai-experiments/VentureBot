import asyncio
import json
import logging
from idea_coach_agent import IdeaCoachAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test():
    """Test the IdeaCoachAgent"""
    print("=== Testing IdeaCoachAgent ===")
    
    # Create an instance of our standalone IdeaCoachAgent
    agent = IdeaCoachAgent()
    
    try:
        # Test with a valid problem statement
        problem_statement = "Generate ideas for a reusable shopping bag."
        ideas = await agent.generate_ideas(problem_statement)
        
        print("\n=== Generated Ideas ===")
        print(json.dumps(ideas, indent=2))
        print(f"Total ideas: {len(ideas)}")
        
        # Verify we have exactly 5 ideas
        assert len(ideas) == 5, f"Expected 5 ideas, got {len(ideas)}"
        
        # Verify each idea has the required fields
        for idea in ideas:
            assert "idea" in idea, "Missing 'idea' field"
            assert "id" in idea, "Missing 'id' field"
        
        print("✅ Test passed: All ideas have required fields")
        
        # Test with a short problem statement
        try:
            print("\n=== Testing short problem statement ===")
            await agent.generate_ideas("Short")
            print("❌ Test failed: Should have raised ValueError")
        except ValueError as e:
            print(f"✅ Test passed: Correctly raised ValueError: {str(e)}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test())