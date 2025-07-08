#!/bin/bash

# VentureBots Deployment Script
# Run this on your remote server to deploy the backend connectivity fix

set -e  # Exit on any error

echo "🚀 Deploying VentureBots Backend Connectivity Fix"
echo "=================================================="

# Step 1: Pull latest changes
echo "📥 Pulling latest changes from main branch..."
git pull origin main

# Step 2: Stop current containers
echo "🛑 Stopping current containers..."
docker compose -f docker/docker-compose.yml down

# Step 3: Build and deploy with fix
echo "🔨 Building and deploying with backend connectivity fix..."
docker compose -f docker/docker-compose.yml up --build -d

# Step 4: Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Step 5: Test deployment
echo "🧪 Testing deployment..."

# Test frontend
if curl -f -s https://venturebots.ncsa.ai > /dev/null; then
    echo "✅ Frontend is accessible at https://venturebots.ncsa.ai"
else
    echo "❌ Frontend test failed"
fi

# Test backend
if curl -f -s https://venturebots.ncsa.ai:8000/docs > /dev/null; then
    echo "✅ Backend is accessible at https://venturebots.ncsa.ai:8000"
else
    echo "❌ Backend test failed - checking if port 8000 is exposed..."
fi

# Test backend connectivity from inside container
echo "🔍 Testing backend from inside frontend container..."
docker exec venturebots-app curl -f -s https://venturebots.ncsa.ai:8000/docs > /dev/null && \
    echo "✅ Frontend can reach backend" || \
    echo "❌ Frontend cannot reach backend"

# Test agent functionality
echo "🤖 Testing agent functionality..."
curl -f -s -X POST https://venturebots.ncsa.ai:8000/apps/manager/users/deploy_test/sessions/deploy_test \
    -H "Content-Type: application/json" \
    -d '{"state": {"test": true}}' > /dev/null && \
    echo "✅ Agent session creation works" || \
    echo "❌ Agent session creation failed"

echo ""
echo "=================================================="
echo "🎉 Deployment completed!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: https://venturebots.ncsa.ai"
echo "   Backend API: https://venturebots.ncsa.ai:8000/docs"
echo ""
echo "🧪 Test the chat functionality:"
echo "   1. Go to https://venturebots.ncsa.ai"
echo "   2. Type 'hello' in the chat"
echo "   3. You should get an AI response (no more 'no text response' error)"
echo ""
echo "📋 If issues persist:"
echo "   - Check logs: docker-compose logs -f"
echo "   - Check backend: curl https://venturebots.ncsa.ai:8000/docs"
echo "   - Verify environment variables in .env file"