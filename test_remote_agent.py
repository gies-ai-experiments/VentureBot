#!/usr/bin/env python3
"""
Test Agent Execution on Remote Server
Run this script on the remote server to test agent response generation
"""

import requests
import json
import time
import sys

def test_remote_agent(base_url="http://localhost:8000"):
    """Test the remote agent execution step by step"""
    
    print("🧪 Testing Remote Agent Execution")
    print("=" * 50)
    
    # Test 1: Check if backend is responding
    print("1. Testing backend connectivity...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is responding")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test 2: List available apps
    print("\n2. Testing app availability...")
    try:
        response = requests.get(f"{base_url}/list-apps", timeout=10)
        apps = response.json()
        print(f"✅ Available apps: {apps}")
        if "manager" not in str(apps):
            print("⚠️  Warning: 'manager' app not found in list")
    except Exception as e:
        print(f"❌ App list failed: {e}")
    
    # Test 3: Create session
    print("\n3. Testing session creation...")
    session_data = {
        "state": {
            "initialized": True,
            "test_mode": True
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/apps/manager/users/remote_test/sessions/remote_test",
            json=session_data,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✅ Session created successfully")
            session_info = response.json()
            print(f"   Session ID: {session_info.get('id')}")
        else:
            print(f"❌ Session creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Test 4: Test direct agent call (non-streaming)
    print("\n4. Testing direct agent call...")
    agent_request = {
        "app_name": "manager",
        "user_id": "remote_test",
        "session_id": "remote_test",
        "body": "hello",
        "new_message": {
            "role": "user",
            "parts": [{"text": "hello"}]
        }
    }
    
    try:
        print("   Sending request to /run endpoint...")
        response = requests.post(
            f"{base_url}/run",
            json=agent_request,
            timeout=30
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Agent responded successfully")
                print(f"   Response type: {type(result)}")
                print(f"   Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                print(f"   Response preview: {str(result)[:200]}...")
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Agent call failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Agent call timed out (30 seconds)")
        return False
    except Exception as e:
        print(f"❌ Agent call error: {e}")
        return False

def test_streaming_endpoint(base_url="http://localhost:8000"):
    """Test the streaming endpoint specifically"""
    
    print("\n" + "=" * 50)
    print("🌊 Testing Streaming Endpoint")
    print("=" * 50)
    
    agent_request = {
        "app_name": "manager",
        "user_id": "remote_test",
        "session_id": "remote_test",
        "body": "hello",
        "new_message": {
            "role": "user",
            "parts": [{"text": "hello"}]
        },
        "streaming": True
    }
    
    try:
        print("Sending streaming request...")
        response = requests.post(
            f"{base_url}/run_sse",
            json=agent_request,
            stream=True,
            timeout=30
        )
        
        print(f"Streaming response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Streaming started, reading events...")
            
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    event_count += 1
                    try:
                        event_data = json.loads(line[6:])
                        print(f"   Event {event_count}: {event_data}")
                        
                        # Check for actual agent response content
                        if event_data.get("content") and event_data["content"].get("parts"):
                            for part in event_data["content"]["parts"]:
                                if part.get("text") and event_data["content"].get("role") == "model":
                                    print(f"✅ Found agent text response: {part['text'][:100]}...")
                                    return True
                        
                        if event_count > 10:  # Limit output
                            print("   ... (truncated)")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"   Invalid JSON in stream: {line}")
                        
            if event_count == 0:
                print("❌ No events received in stream")
                return False
            else:
                print(f"⚠️  Received {event_count} events but no agent text response")
                return False
                
        else:
            print(f"❌ Streaming failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"Testing remote server at: {base_url}")
    
    # Test basic agent execution
    basic_success = test_remote_agent(base_url)
    
    # Test streaming
    streaming_success = test_streaming_endpoint(base_url)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Basic agent execution: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Streaming execution: {'✅ PASS' if streaming_success else '❌ FAIL'}")
    
    if not basic_success and not streaming_success:
        print("\n🔍 Next steps:")
        print("1. Check agent import: cd manager && python3 -c 'from agent import root_agent; print(root_agent.name)'")
        print("2. Check API key: python3 -c 'import os; print(bool(os.getenv(\"ANTHROPIC_API_KEY\")))'")
        print("3. Check ADK logs: Look for import errors or API failures")
        print("4. Test model directly: python3 -c 'from google.adk.models.lite_llm import LiteLlm; m=LiteLlm(\"claude-3-5-haiku-20241022\"); print(\"Model OK\")'")

if __name__ == "__main__":
    main()