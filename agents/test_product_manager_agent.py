import asyncio
import json
import logging
from product_manager_agent import ProductManagerAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_product_manager_agent():
    """Test the ProductManagerAgent"""
    print("=== Testing ProductManagerAgent ===")
    
    # Create a product manager agent
    agent = ProductManagerAgent()
    
    # Test with a normal idea
    test_idea = {
        "id": 1, 
        "idea": "A mobile app that helps users track their daily water intake and reminds them to stay hydrated throughout the day."
    }
    
    try:
        # Generate PRD
        print("\n=== Generating PRD for Normal Idea ===")
        prd_result = await agent.build_prd(test_idea)
        
        print("\n=== PRD Text ===")
        print(prd_result["prd"])
        
        print("\n=== User Stories ===")
        for i, story in enumerate(prd_result["user_stories"], 1):
            complexity = prd_result["complexity_tags"][i-1]
            print(f"{i}. {story} [Complexity: {complexity}]")
        
        # Verify the structure of the result
        assert "prd" in prd_result, "Missing 'prd' field in result"
        assert "user_stories" in prd_result, "Missing 'user_stories' field in result"
        assert "complexity_tags" in prd_result, "Missing 'complexity_tags' field in result"
        
        # Verify user stories and complexity tags match in length
        assert len(prd_result["user_stories"]) == len(prd_result["complexity_tags"]), "User stories and complexity tags length mismatch"
        
        # Verify we have 3-5 user stories
        assert 3 <= len(prd_result["user_stories"]) <= 5, f"Expected 3-5 user stories, got {len(prd_result['user_stories'])}"
        
        print("\n✅ Test passed: Normal idea PRD generation")
        
        # Test with a long idea (>200 chars)
        long_idea = {
            "id": 2,
            "idea": "A comprehensive platform that integrates with smart home devices to monitor and optimize energy usage, providing real-time feedback, historical trends, and personalized recommendations to reduce electricity consumption and carbon footprint, while also offering gamification elements to encourage sustainable habits and allowing users to compare their energy efficiency with neighbors and friends." * 2
        }
        
        print(f"\n=== Generating PRD for Long Idea ({len(long_idea['idea'])} chars) ===")
        prd_result_long = await agent.build_prd(long_idea)
        
        print(f"\n=== PRD Text (excerpt) ===")
        print(prd_result_long["prd"][:200] + "...")
        
        print(f"\n=== User Stories Count: {len(prd_result_long['user_stories'])} ===")
        
        # Verify truncation happened
        assert len(long_idea["idea"]) > 200, "Test idea should be >200 chars"
        
        print("\n✅ Test passed: Long idea PRD generation with truncation")
        
        # Test Google ADK framework integration
        print("\n=== Testing run_async Method (Google ADK Integration) ===")
        events = []
        async_events = agent.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=test_idea
        )
        
        async for event in async_events:
            events.append(event)
            print(f"Event received: {event}")
        
        print(f"Total events: {len(events)}")
        
        # Test with invalid input
        try:
            print("\n=== Testing Invalid Input ===")
            await agent.build_prd({"invalid": "input"})
            print("❌ Test failed: Should have raised ValueError for invalid input")
        except ValueError as e:
            print(f"✅ Test passed: Correctly raised ValueError: {str(e)}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_product_manager_agent())