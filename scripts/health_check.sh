#!/bin/bash

echo "🔍 VentureBots Health Check"
echo "=========================="

# Check if ADK server is responding
echo "📡 Testing ADK server..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ ADK server is responding"
else
    echo "❌ ADK server is not responding"
    exit 1
fi

# Test manager app endpoint
echo "🤖 Testing manager app..."
response=$(curl -s -w "%{http_code}" -X POST \
    http://localhost:8000/apps/manager/users/healthcheck/sessions/healthcheck \
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