# VentureBots Development Guide

## 🚨 Critical Setup & Troubleshooting Guide

This guide prevents the import errors and backend issues that commonly occur when setting up VentureBots.

## 📁 Project Structure Overview

```
VentureBot/
├── main.py                 # Main FastAPI server entry point
├── streamlit_chat.py       # Enhanced frontend with improvements
├── manager/                # Agent implementation directory
│   ├── agent.py           # Root agent definition
│   ├── config.yaml        # Agent configuration
│   ├── tools/
│   │   └── tools.py       # Shared tools for all agents
│   └── sub_agents/
│       ├── onboarding_agent/
│       ├── product_manager/
│       ├── validator_agent/
│       ├── prompt_engineer/
│       └── idea_generator/
├── requirements.txt        # Backend dependencies
├── requirements_streamlit.txt  # Frontend dependencies
└── agent_venv/            # Virtual environment
```

## ⚠️ CRITICAL: Import Path Requirements

### The #1 Issue: Module Import Errors

**PROBLEM:** Sub-agents fail to import tools, causing "No module named 'tools'" errors.

**SOLUTION:** All sub-agents MUST use absolute imports from project root:

```python
# ✅ CORRECT - Works from project root
from manager.tools.tools import claude_web_search

# ❌ WRONG - Causes import errors
from tools.tools import claude_web_search
from ...tools.tools import claude_web_search
from ..tools.tools import claude_web_search
```

### Required Import Pattern for Sub-Agents

Each sub-agent file (`manager/sub_agents/*/agent.py`) must have:

```python
import os
import yaml
import anthropic
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

# ✅ CRITICAL: Use this exact import pattern
from manager.tools.tools import claude_web_search
```

## 🔧 Environment Setup

### 1. Virtual Environment
```bash
# Use the existing agent_venv
source agent_venv/bin/activate

# Verify ADK is installed
pip list | grep google-adk
```

### 2. Environment Variables
Create `.env` file in project root:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Dependencies
```bash
# Backend dependencies (already installed in agent_venv)
pip install -r requirements.txt

# Frontend dependencies (streamlit is in agent_venv)
pip install streamlit requests
```

## 🚀 Correct Startup Sequence

### Backend Startup (Port 8000)

**Option 1: Using main.py (RECOMMENDED)**
```bash
# From project root directory
PORT=8000 python main.py
```

**Option 2: Using ADK CLI (Alternative)**
```bash
# From manager directory
cd manager
adk api_server --port 8000
```

### Frontend Startup (Port 8501)
```bash
# From project root directory
agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501 --server.address 0.0.0.0
```

## 🩺 Pre-Flight Diagnostic Checklist

Run these commands before starting services:

### 1. Test Environment
```bash
echo $ANTHROPIC_API_KEY | cut -c1-10
# Should show: sk-ant-api
```

### 2. Test Agent Imports
```bash
agent_venv/bin/python -c "
import sys
sys.path.insert(0, '/path/to/VentureBot')
from manager.agent import root_agent
print(f'✅ Root agent: {root_agent.name}')
print(f'✅ Sub-agents: {len(root_agent.sub_agents)}')
"
```

### 3. Test Backend Connectivity
```bash
# Start backend, then test
curl -f http://localhost:8000/docs
curl -X POST http://localhost:8000/apps/manager/users/test/sessions/test \
  -H "Content-Type: application/json" \
  -d '{"state": {"initialized": true}}'
```

## 🔍 Common Error Patterns & Fixes

### Error 1: "No module named 'tools'"
```
ModuleNotFoundError: No module named 'tools'
```
**Fix:** Change import in sub-agent files from `from tools.tools import` to `from manager.tools.tools import`

### Error 2: "No module named 'manager'"
```
ModuleNotFoundError: No module named 'manager'
```
**Fix:** Start backend from project root using `main.py`, not from manager directory

### Error 3: "I processed your request but have no text response"
**Root Cause:** Agent import errors causing internal server errors
**Fix:** Check agent imports and restart backend after fixing

### Error 4: "Server running but connection refused"
**Root Cause:** Import errors prevent proper server binding
**Fix:** Check backend logs for import errors, fix imports, restart

## 📋 Development Workflow

### Daily Development Checklist
1. ✅ `cd /path/to/VentureBot` (project root)
2. ✅ `source agent_venv/bin/activate`
3. ✅ Test agent imports first
4. ✅ Start backend: `PORT=8000 python main.py`
5. ✅ Test backend: `curl http://localhost:8000/docs`
6. ✅ Start frontend: `agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501`

### Code Changes Checklist
- ✅ All imports use `from manager.tools.tools import`
- ✅ No relative imports (`../` or `...`)
- ✅ Test imports before committing
- ✅ Restart both services after agent changes

## 🐛 Debug Tools

### Quick Import Test
```python
# Save as test_imports.py
import sys
sys.path.insert(0, '/Users/vishal/Desktop/VentureBot')

try:
    from manager.agent import root_agent
    print('✅ All imports working')
    print(f'Agent: {root_agent.name}')
    print(f'Sub-agents: {[a.name for a in root_agent.sub_agents]}')
except Exception as e:
    print(f'❌ Import failed: {e}')
    import traceback
    traceback.print_exc()
```

### Backend Health Check
```bash
# Save as health_check.sh
curl -f http://localhost:8000/docs && echo "✅ Backend healthy" || echo "❌ Backend issues"
```

### Full Stack Test
```bash
# Save as test_full_stack.sh
echo "Testing session creation..."
curl -X POST http://localhost:8000/apps/manager/users/test/sessions/test \
  -H "Content-Type: application/json" \
  -d '{"state": {"initialized": true}}'

echo -e "\n\nTesting agent response..."
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "manager",
    "user_id": "test",
    "session_id": "test",
    "body": "hello",
    "new_message": {
      "role": "user",
      "parts": [{"text": "hello"}]
    }
  }'
```

## 🏗️ Architecture Notes

### Import Resolution Logic
- ADK scans the project root for agent modules
- When `main.py` runs, project root becomes the Python path
- Sub-agents must import relative to project root, not their own directory
- This is why `from manager.tools.tools import` works but `from tools.tools import` doesn't

### Working Directory Rules
- **Backend:** Must run from project root (`main.py` approach) or manager directory (`adk` CLI)
- **Frontend:** Must run from project root to find `streamlit_chat.py`
- **Development:** Always work from project root directory

## 🎯 Success Indicators

### Backend Working Correctly
- ✅ Server starts without import errors
- ✅ `/docs` endpoint returns HTML
- ✅ Session creation returns JSON with session ID
- ✅ Agent calls return structured responses with text content

### Frontend Working Correctly  
- ✅ Streamlit loads without errors
- ✅ Connection status shows green/connected
- ✅ Chat input accepts messages
- ✅ AI responses appear (not "no text response")

### Full Stack Working
- ✅ Type "hello" → Get welcome message from VentureBot
- ✅ Onboarding workflow starts (asks for name)
- ✅ Multi-agent transfers work smoothly

## 🔄 Restart Procedures

### Quick Restart (Code Changes)
```bash
# Kill both services
pkill -f "python main.py"
pkill -f "streamlit run"

# Restart backend
PORT=8000 nohup python main.py > backend.log 2>&1 &

# Restart frontend  
nohup agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501 > frontend.log 2>&1 &
```

### Clean Restart (Import Issues)
```bash
# Kill all processes
pkill -f "python.*main.py"
pkill -f "streamlit"
pkill -f "adk"

# Test imports first
python test_imports.py

# Start services if imports work
PORT=8000 python main.py &
agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501 &
```

## 📊 Performance Notes

### Expected Startup Times
- **Backend:** 3-5 seconds to bind to port
- **Frontend:** 5-10 seconds to serve first request
- **First AI Response:** 10-15 seconds (model loading)
- **Subsequent Responses:** 3-8 seconds

### Resource Usage
- **Backend:** ~150MB RAM, minimal CPU when idle
- **Frontend:** ~100MB RAM, minimal CPU when idle
- **AI Responses:** CPU spike during generation, network for API calls

---

## 📞 Emergency Quick Fix

If everything breaks:

1. **Stop all processes:** `pkill -f "python.*main\|streamlit\|adk"`
2. **Check project root:** `pwd` should show `.../VentureBot`
3. **Test imports:** `python test_imports.py`
4. **Fix imports if broken:** Change all sub-agent imports to `from manager.tools.tools import`
5. **Restart:** `PORT=8000 python main.py` then `agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501`

**This guide prevents 95% of VentureBots setup issues. Keep it handy!** 🚀