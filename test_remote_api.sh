#!/bin/bash

# Remote API Testing Script
# Usage: ./test_remote_api.sh <remote_server_url>
# Example: ./test_remote_api.sh https://your-app.herokuapp.com

if [ -z "$1" ]; then
    echo "Usage: $0 <remote_server_url>"
    echo "Example: $0 https://your-app.herokuapp.com"
    echo "Example: $0 http://your-server-ip:8000"
    exit 1
fi

REMOTE_URL="$1"
echo "🧪 Testing Remote VentureBots Server: $REMOTE_URL"
echo "=================================================="

# Test 1: Basic connectivity
echo "1. Testing basic connectivity..."
if curl -f -s "$REMOTE_URL/docs" > /dev/null; then
    echo "✅ Server is responding"
else
    echo "❌ Server is not responding at $REMOTE_URL"
    exit 1
fi

# Test 2: List apps
echo -e "\n2. Testing app availability..."
APPS=$(curl -s "$REMOTE_URL/list-apps")
echo "Available apps: $APPS"

# Test 3: Create session
echo -e "\n3. Creating test session..."
SESSION_RESPONSE=$(curl -s -w "%{http_code}" -X POST \
    "$REMOTE_URL/apps/manager/users/remote_test/sessions/remote_test" \
    -H "Content-Type: application/json" \
    -d '{"state": {"initialized": true, "test_mode": true}}')

HTTP_CODE="${SESSION_RESPONSE: -3}"
RESPONSE_BODY="${SESSION_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "✅ Session created successfully"
    echo "Response: $RESPONSE_BODY"
else
    echo "❌ Session creation failed (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

# Test 4: Test non-streaming agent call
echo -e "\n4. Testing agent response (non-streaming)..."
AGENT_RESPONSE=$(curl -s -w "%{http_code}" -X POST \
    "$REMOTE_URL/run" \
    -H "Content-Type: application/json" \
    -d '{
        "app_name": "manager",
        "user_id": "remote_test", 
        "session_id": "remote_test",
        "body": "hello",
        "new_message": {
            "role": "user",
            "parts": [{"text": "hello"}]
        }
    }')

HTTP_CODE="${AGENT_RESPONSE: -3}"
RESPONSE_BODY="${AGENT_RESPONSE%???}"

echo "HTTP Status: $HTTP_CODE"
echo "Response body: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Agent endpoint responded successfully"
    
    # Check if response contains actual text
    if echo "$RESPONSE_BODY" | grep -q '"text"'; then
        echo "✅ Response contains text content"
    else
        echo "❌ Response does not contain text content"
        echo "This explains the 'no text response' error!"
    fi
else
    echo "❌ Agent call failed"
fi

# Test 5: Test streaming endpoint  
echo -e "\n5. Testing streaming endpoint..."
echo "Sending streaming request..."

# Use timeout to limit streaming test
timeout 10s curl -s -X POST \
    "$REMOTE_URL/run_sse" \
    -H "Content-Type: application/json" \
    -d '{
        "app_name": "manager",
        "user_id": "remote_test",
        "session_id": "remote_test", 
        "body": "hello",
        "new_message": {
            "role": "user",
            "parts": [{"text": "hello"}]
        },
        "streaming": true
    }' | head -20

echo -e "\n=================================================="
echo "🔍 Diagnosis Summary:"
echo "- If session creation works: ✅ Backend is running"
echo "- If agent call returns 200 but no text: 🔑 Check API keys"
echo "- If agent call fails completely: 🤖 Check agent imports"
echo "- If streaming shows errors: 📡 Check streaming logic"

echo -e "\nNext steps:"
echo "1. If API key issues: Check ANTHROPIC_API_KEY in deployment"
echo "2. If import issues: Check agent.py imports in container"
echo "3. If model issues: Check LiteLLM model configuration"