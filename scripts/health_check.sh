#!/bin/bash

API_URL=${VENTUREBOT_API_URL:-http://localhost:8000}

echo "🔍 VentureBots Health Check"
echo "=========================="
echo "🌐 Testing server: $API_URL"

# Check FastAPI health endpoint
echo "📡 Checking FastAPI /health..."
if curl -f "$API_URL/health" > /dev/null 2>&1; then
    echo "✅ FastAPI server is responding"
else
    echo "❌ FastAPI server is not responding"
    exit 1
fi

# Create a throwaway session
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/api/sessions" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "healthcheck"}')

SESSION_ID=$(echo "$SESSION_RESPONSE" | python -c 'import sys,json; data=json.load(sys.stdin); print(data.get("session_id", ""))')

if [ -z "$SESSION_ID" ]; then
    echo "❌ Failed to create session"
    echo "Response: $SESSION_RESPONSE"
    exit 1
fi

echo "✅ Session created (ID: $SESSION_ID)"

# Send a simple message
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"ping\"}")

if echo "$CHAT_RESPONSE" | grep -q 'message'; then
    echo "✅ Chat endpoint responded successfully"
else
    echo "❌ Chat endpoint failed"
    echo "Response: $CHAT_RESPONSE"
    exit 1
fi

echo "🎉 All health checks passed!"
exit 0
