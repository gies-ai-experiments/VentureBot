# VentureBots - Claude Code Memory & Development Guide

## Project Overview

VentureBots is an AI-powered entrepreneurship coaching platform built with Google Agent Development Kit (ADK) and Streamlit. It provides multi-agent AI coaching for startup idea generation, validation, product development, and prompt engineering.

## Architecture

### Backend: Google ADK Multi-Agent System
- **Main Entry**: `main.py` - FastAPI server using ADK
- **Root Agent**: `manager/agent.py` - Orchestrates workflow
- **Sub-Agents**: Located in `manager/sub_agents/`
  - `onboarding_agent` - User onboarding and data collection
  - `idea_generator` - Creative idea generation
  - `validator_agent` - Idea validation and feedback
  - `product_manager` - Product development guidance
  - `prompt_engineer` - AI prompt crafting assistance

### Frontend: Chainlit Chat Interface
- **Main File**: `chainlit_app.py` - Professional chat interface built with Chainlit
- **Features**: Real-time streaming, session management, modern UI, mobile-responsive
- **Connection**: Direct integration with ADK backend via REST API
- **Styling**: Custom CSS with VentureBots branding and dark theme

## Critical Setup Requirements

### 1. Import Path Configuration
**MOST IMPORTANT**: All sub-agents must use absolute imports from project root:

```python
# ✅ CORRECT - Required for ADK module discovery
from manager.tools.tools import claude_web_search

# ❌ WRONG - Causes "No module named" errors
from tools.tools import claude_web_search
from ...tools.tools import claude_web_search
```

### 2. Working Directory Rules
- **Backend**: Must run from project root using `main.py`
- **Frontend**: Must run from project root
- **Development**: Always work from `/Users/vishal/Desktop/VentureBot`

### 3. Environment Setup
```bash
# Virtual environment
source agent_venv/bin/activate

# Environment variables (.env file required)
ANTHROPIC_API_KEY=sk-ant-api03-[your-key-here]

# Dependencies already installed in agent_venv:
# - google-adk==0.4.0
# - anthropic==0.50.0
# - streamlit (and all requirements)
```

## Correct Startup Sequence

### Backend (Port 8000)
```bash
cd /Users/vishal/Desktop/VentureBot
PORT=8000 python main.py
```

### Frontend (Port 8501)
```bash
cd /Users/vishal/Desktop/VentureBot
source agent_venv/bin/activate && chainlit run chainlit_app.py --port 8501
```

### Pre-Flight Check
```bash
# Always run this first to catch import issues
python test_imports.py
```

## Common Issues & Solutions

### Issue 1: "No module named 'tools'" or "No module named 'manager'"
**Root Cause**: Incorrect import paths in sub-agent files
**Solution**: 
1. Check all files in `manager/sub_agents/*/agent.py`
2. Ensure imports use `from manager.tools.tools import claude_web_search`
3. Run `python test_imports.py` to verify

### Issue 2: "I processed your request but have no text response"
**Root Cause**: Backend agent import failures causing internal server errors
**Solution**:
1. Check backend logs for import errors
2. Fix import paths in sub-agents
3. Restart backend: `PORT=8000 python main.py`

### Issue 3: Backend shows "running" but connection refused
**Root Cause**: Import errors prevent proper server binding
**Solution**:
1. Stop all processes: `pkill -f "python.*main\|streamlit\|adk"`
2. Test imports: `python test_imports.py`
3. Fix any import errors found
4. Restart services

## File Structure & Key Components

```
VentureBot/
├── main.py                 # ✅ Main backend entry point
├── streamlit_chat.py       # ✅ Enhanced frontend
├── test_imports.py         # ✅ Diagnostic tool
├── DEVELOPMENT_GUIDE.md    # ✅ Detailed troubleshooting
├── CLAUDE.md              # ✅ This file
├── .env                   # ✅ API keys
├── agent_venv/            # ✅ Virtual environment
├── manager/               # ✅ Agent implementation
│   ├── agent.py          # Root agent
│   ├── config.yaml       # Agent configuration
│   ├── tools/tools.py    # Shared utilities
│   └── sub_agents/       # Individual agent modules
└── requirements*.txt      # Dependencies
```

## Development Workflow

### Daily Development Checklist
1. `cd /Users/vishal/Desktop/VentureBot`
2. `python test_imports.py` (verify all imports work)
3. `PORT=8000 python main.py` (start backend)
4. `agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501` (start frontend)
5. Test at http://localhost:8501

### Code Changes Checklist
- Ensure imports use `from manager.tools.tools import`
- Test imports before committing: `python test_imports.py`
- Restart both services after agent changes
- Verify full workflow: type "hello" → should get VentureBot welcome

## API Endpoints

### Backend (localhost:8000)
- `/docs` - API documentation
- `/apps/manager/users/{user_id}/sessions/{session_id}` - Session creation
- `/run` - Non-streaming agent execution
- `/run_sse` - Streaming agent execution (used by frontend)

### Frontend (localhost:8501)
- Main Streamlit interface with enhanced features
- Real-time chat with AI agents
- Mobile-responsive design
- Chat history and export functionality

## Agent Workflow

1. **User Input** → Manager Agent
2. **Manager** → Transfers to appropriate sub-agent
3. **Sub-Agent** → Processes request and responds
4. **Response** → Sent back through manager to frontend

Example flow:
- "hello" → Manager → Onboarding Agent → Welcome message
- User provides name → Onboarding → Idea Generator → Generate ideas
- User selects idea → Validator → Product Manager → etc.

## Testing & Verification

### Quick Health Check
```bash
# Backend health
curl -f http://localhost:8000/docs

# Frontend health  
curl -s http://localhost:8501 | grep -o "<title>.*</title>"

# Full stack test
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"app_name": "manager", "user_id": "test", "session_id": "test", "body": "hello", "new_message": {"role": "user", "parts": [{"text": "hello"}]}}'
```

### Expected Success Indicators
- ✅ Import test passes: `python test_imports.py`
- ✅ Backend starts without errors and binds to port 8000
- ✅ Frontend loads and shows connection status
- ✅ Chat responds with actual AI text (not "no text response")
- ✅ Multi-agent workflow functions (onboarding → idea generation → etc.)

## Performance Notes
- **First AI Response**: 10-15 seconds (model loading)
- **Subsequent Responses**: 3-8 seconds
- **Memory Usage**: ~250MB total for both services
- **Dependencies**: All critical packages installed in agent_venv

## Emergency Recovery
If everything breaks:
1. `pkill -f "python.*main\|streamlit"`
2. `cd /Users/vishal/Desktop/VentureBot`
3. `python test_imports.py` (fix any import errors)
4. `PORT=8000 python main.py &`
5. `agent_venv/bin/python -m streamlit run streamlit_chat.py --server.port 8501 &`

## Key Lessons Learned
- ADK module discovery requires absolute imports from project root
- Import errors cause silent failures that appear as "no text response"
- Always test imports before starting services
- Working directory matters for ADK agent discovery
- Sub-agent import paths are the #1 source of issues

---

**Status**: ✅ Fully operational with clean, modern frontend and working multi-agent backend
**Last Updated**: July 2025
**Next Session**: Use `python test_imports.py` first, then start services as documented above

### Latest Update: Chainlit Frontend Migration
- **Replaced Streamlit with Chainlit** - Industry-standard for conversational AI
- **Professional chat interface** - Built specifically for AI coaching applications  
- **Eliminated Streamlit issues** - No more text input visibility or connection problems
- **Modern design system** - Custom CSS with VentureBots branding
- **Real-time streaming** - Proper SSE integration with Google ADK backend
- **Session management** - Robust user session handling
- **Mobile-responsive** - Optimized for all devices