#!/usr/bin/env python3
"""
Test the live enhanced market intelligence system by sending requests to the running backend.
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration - can be overridden via environment variables
ADK_SERVER_URL = os.getenv("ADK_SERVER_URL", "http://localhost:8000")

def test_backend_health():
    """Test if backend is running and healthy"""
    try:
        response = requests.get(f"{ADK_SERVER_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def create_session():
    """Create a new session for testing"""
    try:
        url = f"{ADK_SERVER_URL}/apps/manager/users/test_user/sessions/test_session"
        response = requests.post(url, timeout=10)
        if response.status_code == 200:
            print("✅ Session created successfully")
            return True
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False

def send_message_to_agent(message):
    """Send a message to the agent and get response"""
    try:
        url = f"{ADK_SERVER_URL}/run"
        payload = {
            "app_name": "manager",
            "user_id": "test_user", 
            "session_id": "test_session",
            "body": message,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        }
        
        print(f"📤 Sending: '{message}'")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if 'content' in result and 'parts' in result['content'] and result['content']['parts']:
                agent_response = result['content']['parts'][0]['text']
                print(f"📥 Response received ({len(agent_response)} chars)")
                return agent_response
            else:
                print("❌ No response text found in result")
                return None
        else:
            print(f"❌ Request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None

def test_full_workflow():
    """Test the complete enhanced validation workflow"""
    print("🧪 Testing Enhanced Market Intelligence Workflow")
    print("=" * 60)
    
    # Step 1: Start with hello
    print("\n1️⃣ Testing initial greeting...")
    response = send_message_to_agent("hello")
    if not response:
        return False
    print(f"   Response preview: {response[:150]}...")
    
    # Step 2: Provide user info (simulate onboarding)
    print("\n2️⃣ Testing onboarding...")
    time.sleep(2)
    response = send_message_to_agent("My name is Alex. I'm interested in AI and fitness technology. I love developing innovative apps.")
    if not response:
        return False
    print(f"   Response preview: {response[:150]}...")
    
    # Step 3: Request idea generation
    print("\n3️⃣ Testing idea generation...")
    time.sleep(2)
    response = send_message_to_agent("Please generate some startup ideas for me")
    if not response:
        return False
    print(f"   Response preview: {response[:150]}...")
    
    # Step 4: Select an idea for validation (this should trigger enhanced analysis)
    print("\n4️⃣ Testing ENHANCED MARKET INTELLIGENCE...")
    time.sleep(2)
    
    print("🚀 This is the key test - selecting idea #1 should trigger:")
    print("   • Real web search for market intelligence")
    print("   • Multi-dimensional scoring analysis") 
    print("   • Rich visual dashboard generation")
    print("   • Comprehensive competitor and market gap analysis")
    print("\n⏳ Starting enhanced validation (may take 15-30 seconds)...")
    
    start_time = time.time()
    response = send_message_to_agent("I'd like to validate idea #1")
    end_time = time.time()
    
    if not response:
        print("❌ Enhanced validation failed - no response")
        return False
    
    duration = end_time - start_time
    print(f"✅ Enhanced validation completed in {duration:.1f} seconds")
    
    # Analyze the response for enhanced features
    enhanced_features = {
        "Market Analysis Header": "MARKET ANALYSIS:" in response,
        "Overall Assessment": "OVERALL ASSESSMENT:" in response,
        "Detailed Scores": "DETAILED SCORES:" in response,
        "Progress Bars": "████" in response,
        "Competitor Analysis": "COMPETITORS" in response,
        "Market Opportunities": "OPPORTUNITIES" in response,
        "Strategic Recommendations": "RECOMMENDATIONS" in response,
        "Confidence Score": "CONFIDENCE:" in response
    }
    
    print(f"\n📊 Enhanced Features Analysis:")
    for feature, present in enhanced_features.items():
        status = "✅" if present else "❌"
        print(f"   {status} {feature}")
    
    # Show response preview
    print(f"\n📋 Response Preview (first 500 chars):")
    print("-" * 50)
    print(response[:500])
    if len(response) > 500:
        print("...")
    print("-" * 50)
    
    # Count enhanced features
    enhanced_count = sum(enhanced_features.values())
    total_features = len(enhanced_features)
    
    print(f"\n🎯 Enhanced Features: {enhanced_count}/{total_features}")
    
    if enhanced_count >= 6:  # At least 6/8 features should be present
        print("🎉 Enhanced market intelligence system working correctly!")
        return True
    else:
        print("⚠️ Enhanced system may not be fully working - check features above")
        return False

def main():
    """Run complete local testing"""
    print("🧪 VentureBot Enhanced Market Intelligence - Local Testing")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Backend health
    print("\n🔍 Testing Backend Health...")
    if not test_backend_health():
        print("❌ Backend not running. Please start with: PORT=8000 python main.py")
        return
    
    # Test 2: Session creation
    print("\n🔗 Testing Session Creation...")
    if not create_session():
        print("❌ Cannot create session. Check backend logs.")
        return
    
    # Test 3: Full workflow with enhanced validation
    print("\n🚀 Testing Enhanced Market Intelligence Workflow...")
    success = test_full_workflow()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 Local testing completed successfully!")
        print("💡 The enhanced market intelligence system is working correctly.")
        print("🎯 Users will now get comprehensive market analysis with:")
        print("   • Real competitor intelligence")
        print("   • Market opportunity scoring")
        print("   • Strategic recommendations") 
        print("   • Visual progress indicators")
        print("   • Professional market insights")
    else:
        print("⚠️  Some issues detected during testing.")
        print("🔧 Check the response analysis above for details.")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()