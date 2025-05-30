import asyncio
import json
import logging
from validation_agent import ValidationAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_validation_agent():
    """Test the ValidationAgent"""
    print("=== Testing ValidationAgent ===")
    
    # Create a validation agent with mock search API credentials
    agent = ValidationAgent(
        search_api_key="nwTUxMTTFaZGcpPsa3P3wakm", 
        search_endpoint="https://www.searchapi.io/api/v1/search"
    )
    
    # Test ideas from IdeaCoachAgent
    test_ideas = [
        {"id": 1, "idea": "Reusable shopping bag made from recycled plastic bottles"},
        {"id": 2, "idea": "Canvas tote with reinforced handles and a waterproof bottom"},
        {"id": 3, "idea": "Multi-compartment shopping bag with separate sections for different items"},
        {"id": 4, "idea": "Expandable mesh shopping bag that adjusts to different sizes"},
        {"id": 5, "idea": "Self-cleaning antimicrobial shopping bag with UV sanitization"}
    ]
    
    try:
        # Score the ideas
        print("\n=== Scoring Ideas ===")
        scored_ideas = await agent.score_ideas(test_ideas)
        print(json.dumps(scored_ideas, indent=2))
        
        # Verify each idea has the required score fields
        if isinstance(scored_ideas, list):
            for idea in scored_ideas:
                assert "id" in idea, "Missing 'id' field"
                assert "impact" in idea, "Missing 'impact' field"
                assert "feasibility" in idea, "Missing 'feasibility' field"
                assert "innovation" in idea, "Missing 'innovation' field"
                
                # Verify scores are within range [0, 10]
                assert 0 <= idea["impact"] <= 10, f"Impact score out of range: {idea['impact']}"
                assert 0 <= idea["feasibility"] <= 10, f"Feasibility score out of range: {idea['feasibility']}"
                assert 0 <= idea["innovation"] <= 10, f"Innovation score out of range: {idea['innovation']}"
            
            print("✅ Test passed: All scored ideas have required fields and valid scores")
        else:
            print("❌ Test failed: Expected a list of scored ideas")
        
        # Test edge cases
        
        # 1. Empty ideas list
        print("\n=== Testing Empty Ideas List ===")
        try:
            await agent.score_ideas([])
            print("❌ Test failed: Should have raised ValueError for empty ideas list")
        except ValueError as e:
            print(f"✅ Test passed: Correctly raised ValueError: {str(e)}")
        
        # 2. Invalid idea (missing fields)
        print("\n=== Testing Invalid Idea (Missing Fields) ===")
        partial_results = await agent.score_ideas([
            {"id": 6},  # Missing "idea" field
            {"idea": "This idea has no ID"}  # Missing "id" field
        ])
        print(json.dumps(partial_results, indent=2))
        
        # 3. Test Google ADK framework integration
        print("\n=== Testing run_async Method (Google ADK Integration) ===")
        events = []
        async_events = agent.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=test_ideas
        )
        
        async for event in async_events:
            events.append(event)
            print(f"Event received: {event}")
        
        print(f"Total events: {len(events)}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_validation_agent())