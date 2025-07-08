#!/bin/bash

# Configuration - can be overridden via environment variables
ADK_SERVER_URL=${ADK_SERVER_URL:-http://localhost:8000}

echo "🔍 VentureBots Health Check"
echo "=========================="
echo "🌐 Testing server: $ADK_SERVER_URL"

# Check if ADK server is responding
echo "📡 Testing ADK server..."
if curl -f "$ADK_SERVER_URL/docs" > /dev/null 2>&1; then
    echo "✅ ADK server is responding"
else
    echo "❌ ADK server is not responding"
    exit 1
fi

# Test manager app endpoint
echo "🤖 Testing manager app..."
response=$(curl -s -w "%{http_code}" -X POST \
    "$ADK_SERVER_URL/apps/manager/users/healthcheck/sessions/healthcheck" \
    -H "Content-Type: application/json" \
    -d '{"state": {"test": true}}' -o /dev/null)

if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
    echo "✅ Manager app is working"
else
    echo "❌ Manager app failed (HTTP $response)"
    exit 1
fi

echo "🎉 All health checks passed!"
exit 0