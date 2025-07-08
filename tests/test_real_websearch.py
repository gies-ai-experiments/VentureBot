#!/usr/bin/env python3
"""
Test script for real web search functionality.
"""

import os
import sys
import asyncio
import anthropic
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from manager.tools.tools import claude_web_search, validation_circuit_breaker
from manager.sub_agents.validator_agent.agent import ClaudeWebSearchValidator
from unittest.mock import Mock, AsyncMock

def test_real_web_search():
    """Test the real web search functionality"""
    print("🔍 Testing Real Web Search Implementation")
    print("=" * 50)
    
    # Create Anthropic client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found")
        return False
    
    anthropic_client = anthropic.Anthropic(api_key=api_key)
    
    # Test cases
    test_queries = [
        "social media app",
        "AI-powered fitness tracker", 
        "blockchain marketplace",
        "meditation app"
    ]
    
    print(f"Testing {len(test_queries)} queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        
        try:
            start_time = datetime.now()
            result = claude_web_search(query, anthropic_client)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if "results" in result and len(result["results"]) > 0:
                print(f"   ✅ Success in {duration:.1f}s")
                print(f"   📊 Found {len(result['results'])} results")
                
                # Show first result
                first_result = result["results"][0]
                print(f"   📝 Title: {first_result['title']}")
                print(f"   📄 Content: {first_result['content'][:100]}...")
                
            else:
                print(f"   ⚠️ No results returned in {duration:.1f}s")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    print(f"\n🔧 Circuit breaker status: {'Open' if not validation_circuit_breaker.can_proceed() else 'Closed'}")
    print(f"   Failure count: {validation_circuit_breaker.failure_count}")
    
    return True

async def test_validator_agent_integration():
    """Test the validator agent with real web search"""
    print("\n🤖 Testing Validator Agent Integration")
    print("=" * 50)
    
    # Create mock conversation
    mock_conversation = Mock()
    mock_conversation.send_message = AsyncMock()
    
    # Create validator agent
    validator = ClaudeWebSearchValidator(name="test_validator")
    
    # Test memory with selected idea
    memory = {
        "SelectedIdea": {
            "id": 1,
            "idea": "AI-powered meditation and mindfulness app"
        }
    }
    
    print("Testing validator agent with real web search...")
    
    try:
        start_time = datetime.now()
        result = await validator.handle(mock_conversation, memory)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Validator completed in {duration:.1f}s")
        
        if result and len(result) > 0:
            score = result[0]
            print(f"📊 Validation Results:")
            print(f"   Feasibility: {score['feasibility']}")
            print(f"   Innovation: {score['innovation']}")
            print(f"   Overall Score: {score['score']}")
            print(f"   Notes: {score['notes']}")
            
            # Check if result was stored in memory
            if "Validator" in memory:
                print("✅ Results properly stored in memory")
            else:
                print("❌ Results not stored in memory")
                
        else:
            print("❌ No validation results returned")
            
        # Check conversation calls
        if mock_conversation.send_message.called:
            call_count = mock_conversation.send_message.call_count
            print(f"✅ Sent {call_count} messages to user")
        else:
            print("❌ No messages sent to user")
            
    except Exception as e:
        print(f"❌ Validator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return True

def main():
    """Run all tests"""
    print("🧪 VentureBot Real Web Search Tests")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Direct web search
    test_real_web_search()
    
    # Test 2: Validator agent integration  
    asyncio.run(test_validator_agent_integration())
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()