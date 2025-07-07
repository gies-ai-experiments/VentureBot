# VentureBot Agent System Analysis & Troubleshooting Template

## 1. System Architecture Overview

### Component Hierarchy

```
VentureBot System
├── Frontend (Port 8501)
│   └── chainlit_app.py
│       ├── VentureBotSession class
│       ├── Session management
│       ├── Streaming communication
│       └── Error recovery
│
├── Backend (Port 8000)
│   └── main.py (FastAPI + Google ADK)
│       ├── ADK server setup
│       ├── Session persistence (SQLite)
│       ├── CORS configuration
│       └── API endpoints
│
└── Agent System
    ├── manager/agent.py (Root Orchestrator)
    │   ├── Memory coordination
    │   ├── Agent transfer logic
    │   └── Workflow management
    │
    ├── manager/sub_agents/
    │   ├── onboarding_agent/
    │   │   ├── User data collection
    │   │   ├── Retry mechanisms
    │   │   └── Profile structuring
    │   │
    │   ├── idea_generator/
    │   │   ├── Creative generation
    │   │   ├── BADM 350 concept integration
    │   │   └── JSON formatting
    │   │
    │   ├── validator_agent/
    │   │   ├── Web search integration
    │   │   ├── Feasibility scoring
    │   │   └── Innovation assessment
    │   │
    │   ├── product_manager/
    │   │   ├── PRD generation
    │   │   ├── Market research
    │   │   └── User story creation
    │   │
    │   └── prompt_engineer/
    │       ├── No-code prompt generation
    │       ├── UI/UX specifications
    │       └── Technical integration
    │
    ├── manager/tools/tools.py (Shared Utilities)
    │   ├── claude_web_search()
    │   ├── validate_user_input()
    │   └── format_user_profile()
    │
    └── manager/config.yaml (System Configuration)
        ├── Model: claude-3-5-haiku-20241022
        ├── Parameters: num_ideas, max_loops, thresholds
        └── Persistence: user_profiles.json
```

### Critical Dependencies & Import Relationships

```python
# Critical Import Pattern (MUST be absolute from project root)
✅ CORRECT:
from manager.tools.tools import claude_web_search
from manager.sub_agents.onboarding_agent.agent import OnboardingAgent

❌ INCORRECT (causes "No module named" errors):
from tools.tools import claude_web_search
from ...tools.tools import claude_web_search
```

**ADK Integration Points:**
- `main.py` → Google ADK FastAPI server
- `manager/agent.py` → ADK conversation interface
- All sub-agents → ADK agent framework
- Session management → ADK session persistence

### Data Flow Diagrams

#### User Input Flow
```
User Input (Chainlit) 
    ↓
HTTP POST to /run_sse (Backend)
    ↓
ADK Session Management
    ↓
Manager Agent (agent.py)
    ↓
Sub-Agent Selection & Transfer
    ↓
Sub-Agent Processing
    ↓
Response Generation
    ↓
SSE Stream to Frontend
    ↓
Chainlit UI Update
```

#### Memory Management Flow
```
Manager Agent Memory Coordination
    ↓
memory['user_input'] → Onboarding Agent
    ↓
memory['IdeaCoach'] → Idea Generator (stores 5 ideas)
    ↓
memory['SelectedIdea'] → Validator Agent
    ↓
memory['Validator'] → Product Manager (validation scores)
    ↓
memory['PRD'] → Prompt Engineer (product requirements)
    ↓
memory['BuilderPrompt'] → Final output
```

### Agent Workflow Sequences

#### Complete User Journey
1. **Initial Connection**
   - Frontend establishes session via `/apps/manager/users/{user_id}/sessions/{session_id}`
   - Backend creates ADK session with SQLite persistence
   - Manager agent initializes with empty memory

2. **Onboarding Phase**
   - User sends "hello" → Manager → Onboarding Agent
   - Onboarding collects: name, experience, industry, goals
   - Timeout: 300 seconds, Max retries: 3
   - Data stored in `memory['user_input']`

3. **Idea Generation Phase**
   - User profile triggers transfer to Idea Generator
   - Generates 5 distinct app ideas with technical concepts
   - Ideas stored as JSON array in `memory['IdeaCoach']`
   - User presented with numbered list for selection

4. **Validation Phase**
   - User selection stored in `memory['SelectedIdea']`
   - Validator Agent performs web search analysis
   - Scoring algorithm: Feasibility + Innovation metrics
   - Results stored in `memory['Validator']`

5. **Product Management Phase**
   - Validated idea triggers Product Manager
   - Web search for market context
   - PRD generation with user stories
   - Document stored in `memory['PRD']`

6. **Prompt Engineering Phase**
   - PRD triggers Prompt Engineer
   - Generates no-code builder prompt (max 10,000 tokens)
   - Final output in `memory['BuilderPrompt']`

### Memory Management Patterns

#### Memory Key Structure
```python
memory = {
    'user_input': {
        'name': str,
        'experience': str,
        'industry': str,
        'goals': str
    },
    'IdeaCoach': [
        {
            'idea': str,
            'technical_concept': str,
            'description': str
        }
    ],
    'SelectedIdea': {
        'idea': str,
        'user_selection': int
    },
    'Validator': {
        'feasibility_score': float,
        'innovation_score': float,
        'overall_score': float,
        'recommendation': str
    },
    'PRD': {
        'overview': str,
        'user_personas': list,
        'user_stories': list,
        'requirements': dict,
        'success_metrics': list
    },
    'BuilderPrompt': str
}
```

#### Memory Persistence Rules
- Memory persists across agent transfers within session
- Session data stored in SQLite database
- Memory cleanup on session termination
- Error recovery maintains partial memory state

## 2. Component Analysis

### Backend Components

#### main.py - FastAPI Server (Entry Point)
**Location**: `/Users/vishal/Desktop/VentureBot/main.py`

**Purpose**: ADK-powered FastAPI server initialization

**Key Functions**:
```python
def get_fast_api_app():
    # Creates ADK FastAPI application
    # Configures CORS for frontend communication
    # Sets up session database persistence
    # Returns configured FastAPI instance
```

**Configuration Variables**:
- `AGENT_DIR`: Project root (defaults to current directory)
- `SESSION_DB_URL`: SQLite database path
- `ALLOWED_ORIGINS`: CORS origins (currently allows all)
- `SERVE_WEB_INTERFACE`: ADK web UI toggle

**Critical Requirements**:
- Must run from project root directory
- Port 8000 (configurable via PORT environment variable)
- Requires ANTHROPIC_API_KEY environment variable

**Error Indicators**:
- Import errors prevent server binding
- "Connection refused" suggests import failures
- Missing API key causes authentication errors

#### manager/agent.py - Root Orchestrator
**Location**: `/Users/vishal/Desktop/VentureBot/manager/agent.py`

**Purpose**: Central workflow coordinator and memory manager

**Key Responsibilities**:
- Agent selection and transfer logic
- Memory state management across sub-agents
- Technical concept integration (BADM 350)
- Error handling and recovery

**Memory Coordination**:
```python
# Memory keys managed by root agent
memory['user_input']     # Onboarding data
memory['IdeaCoach']      # Generated ideas
memory['SelectedIdea']   # User selection
memory['Validator']      # Validation results  
memory['PRD']            # Product requirements
memory['BuilderPrompt']  # Final output
```

**Configuration Source**: `manager/config.yaml`

**Error Handling**: Delegates to ADK framework error mechanisms

#### Sub-Agents Detailed Analysis

##### Onboarding Agent
**Location**: `/Users/vishal/Desktop/VentureBot/manager/sub_agents/onboarding_agent/agent.py`

**Purpose**: User welcome, data collection, and profile structuring

**Key Methods**:
```python
class OnboardingAgent:
    def handle(conversation, memory):
        # Main conversation handler
        # Collects required profile data
        # Implements retry logic for missing fields
        
    def handle_required_question(conversation, memory, question, field_name):
        # Retry mechanism for required fields
        # Timeout: 300 seconds
        # Max attempts: 3
```

**Data Collection Pattern**:
1. Welcome message with VentureBot branding
2. Sequential data collection: name, experience, industry, goals
3. Retry logic for required fields
4. Structured profile storage

**Error Handling**:
- Timeout management (300 seconds per question)
- Retry mechanism (max 3 attempts per field)
- Graceful fallback for optional data
- Comprehensive logging to `onboarding.log`

**Dependencies**:
```python
from anthropic import Anthropic
from manager.tools.tools import claude_web_search
```

##### Idea Generator
**Location**: `/Users/vishal/Desktop/VentureBot/manager/sub_agents/idea_generator/agent.py`

**Purpose**: Creative app idea generation with technical concept integration

**Key Features**:
- Generates exactly 5 distinct app ideas
- Integrates BADM 350 technical concepts
- JSON array output format
- User profile-based customization

**Technical Concepts Integrated**:
- Network Effects
- SaaS Business Models
- Data-Driven Decision Making
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)

**Output Format**:
```json
[
    {
        "idea": "App concept name",
        "technical_concept": "BADM 350 concept",
        "description": "Detailed description"
    }
]
```

**Error Handling**: Basic exception handling with delegation to manager

##### Validator Agent
**Location**: `/Users/vishal/Desktop/VentureBot/manager/sub_agents/validator_agent/agent.py`

**Purpose**: Idea validation using web search and scoring algorithms

**Key Methods**:
```python
class ClaudeWebSearchValidator:
    def handle(conversation, memory):
        # Core validation logic
        # Web search integration
        # Scoring algorithm implementation
```

**Validation Algorithm**:
```python
# Scoring based on web search hit count
search_hits = len(search_results)
feasibility_score = min(search_hits / 5, 1.0)  # Existing solutions
innovation_score = max(1.0 - search_hits / 10, 0.0)  # Uniqueness
overall_score = 0.6 * feasibility_score + 0.4 * innovation_score
```

**Web Search Integration**:
- Uses `claude_web_search` tool from manager.tools.tools
- Search query based on idea description
- Result count analysis for scoring

**Output Format**:
```json
{
    "feasibility_score": float,
    "innovation_score": float,
    "overall_score": float,
    "recommendation": "proceed|revise|abandon"
}
```

**Error Handling**: Search failure handling with fallback responses

##### Product Manager
**Location**: `/Users/vishal/Desktop/VentureBot/manager/sub_agents/product_manager/agent.py`

**Purpose**: Product Requirements Document (PRD) creation with market research

**Key Features**:
- Web search-based market context
- Structured PRD generation
- User story creation
- Success metrics definition

**PRD Structure**:
```json
{
    "overview": "Value proposition and market positioning",
    "user_personas": [
        {
            "name": "Primary User",
            "demographics": "...",
            "needs": "...",
            "pain_points": "..."
        }
    ],
    "user_stories": [
        "As a [user type], I want [functionality] so that [benefit]"
    ],
    "functional_requirements": {
        "core_features": [],
        "nice_to_have": []
    },
    "non_functional_requirements": {
        "performance": "...",
        "security": "...",
        "scalability": "..."
    },
    "success_metrics": [
        "User acquisition rate",
        "Feature adoption metrics",
        "Business impact KPIs"
    ]
}
```

**Web Search Integration**: Market research for competitive analysis

**Error Handling**: API error handling with detailed error messages

##### Prompt Engineer
**Location**: `/Users/vishal/Desktop/VentureBot/manager/sub_agents/prompt_engineer/agent.py`

**Purpose**: No-code app builder prompt generation

**Key Features**:
- Frontend-only prompt optimization
- UI/UX specification generation
- Technical integration guidelines
- Token limit: 10,000 maximum

**Prompt Structure**:
```
App Builder Prompt (Max 10,000 tokens):
├── Core Screen Definitions
├── User Flow Specifications  
├── UI Element Definitions
├── Technical Integration Guidelines
└── Responsive Design Requirements
```

**Output Optimization**:
- Frontend-focused specifications
- No-code platform compatibility
- Visual design guidelines
- Interactive element definitions

**Error Handling**: Generation failure handling with error details

### Frontend Integration

#### chainlit_app.py - Modern Chat Interface
**Location**: `/Users/vishal/Desktop/VentureBot/chainlit_app.py`

**Purpose**: Professional chat interface built with Chainlit

**Key Classes**:
```python
class VentureBotSession:
    def __init__(self):
        # Session initialization
        # Unique ID generation
        # Connection state management
        
    async def create_session(self):
        # ADK session creation
        # Error handling for connection failures
        
    async def send_message_stream(self, message):
        # Streaming communication with backend
        # SSE response handling
        # Real-time UI updates
```

**Session Management**:
- Unique user/session ID generation using UUID4
- Session state persistence across conversations
- Connection error recovery mechanisms
- Timeout handling for backend communication

**Streaming Implementation**:
```python
# Server-Sent Events (SSE) integration
async for line in response.aiter_lines():
    if line.startswith('data: '):
        chunk = self._parse_streaming_response(line)
        if chunk:
            await cl.Message(content=chunk).send()
```

**User Experience Features**:
- Loading indicators and status messages
- Error recovery with user-friendly messages
- Professional VentureBot branding
- Real-time streaming responses
- Mobile-responsive design

**API Integration**:
- RESTful communication with ADK backend
- Proper error handling for HTTP requests
- Session initialization via `/apps/manager/users/{user_id}/sessions/{session_id}`
- Message streaming via `/run_sse` endpoint

**Error Handling**:
```python
# Connection failure recovery
try:
    response = await self.send_message_stream(message)
except Exception as e:
    await cl.Message(
        content="I apologize, but I'm having trouble connecting to my backend services. Please try again in a moment."
    ).send()
```

### Shared Resources

#### manager/tools/tools.py - Shared Utilities
**Location**: `/Users/vishal/Desktop/VentureBot/manager/tools/tools.py`

**Purpose**: Common utilities shared across all agents

**Key Functions**:
```python
def claude_web_search(query: str) -> str:
    # Web search using Claude's native capabilities
    # Tool use detection and response parsing
    # Fallback to direct response if no tool use
    # Comprehensive error handling and logging

def validate_user_input(input_data: dict) -> bool:
    # Input validation for user profile data
    # Required field checking
    # Data type validation

def format_user_profile(user_data: dict) -> str:
    # Profile formatting for agent consumption
    # Structured text generation
    # Consistent formatting across agents
```

**Web Search Implementation Details**:
```python
# Claude tool use pattern detection
if '**Web Search Results**' in response or 'search_results' in response.lower():
    # Parse structured search results
elif response.strip():
    # Use direct response as search results
else:
    # Fallback error handling
```

**Error Handling**: Extensive logging and exception handling with detailed error messages

**Dependencies**:
```python
from anthropic import Anthropic
import logging
import json
```

#### manager/config.yaml - System Configuration
**Location**: `/Users/vishal/Desktop/VentureBot/manager/config.yaml`

**Purpose**: Centralized configuration for all agents

**Key Settings**:
```yaml
model: "claude-3-5-haiku-20241022"  # LLM model specification
num_ideas: 5                        # Number of ideas to generate
max_loops: 3                        # Maximum iteration count
validation_threshold: 0.7           # Validation score threshold
persistence:
  user_profiles: "user_profiles.json"  # User data persistence
```

**Configuration Usage**:
- Model selection for all agents
- Behavior parameter tuning
- Threshold configuration for decision logic
- Persistence settings for data storage

#### Environment Variables & Dependencies

**Critical Environment Variables**:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-[your-key-here]

# Optional (with defaults)
ADK_BACKEND_URL=http://localhost:8000  # Frontend-backend communication
PORT=8000                              # Server port
```

**Dependency Requirements**:
```
# Core dependencies (installed in agent_venv)
google-adk==0.4.0                     # Agent Development Kit
anthropic==0.50.0                     # Claude API client
chainlit                              # Frontend framework
fastapi                               # Backend framework
uvicorn                               # ASGI server
```

**Python Environment**:
- Python 3.8+ required
- Virtual environment: `agent_venv/`
- Package installation via requirements files

**File Structure Requirements**:
```
VentureBot/                           # Project root (CRITICAL)
├── main.py                          # Backend entry point
├── chainlit_app.py                  # Frontend entry point
├── agent_venv/                      # Virtual environment
├── manager/                         # Agent implementation
│   ├── agent.py                     # Root agent
│   ├── config.yaml                  # Configuration
│   ├── tools/                       # Shared utilities
│   └── sub_agents/                  # Individual agents
├── .env                             # Environment variables
└── requirements*.txt                # Dependencies
```