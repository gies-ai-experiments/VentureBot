# VentureBots - AI Entrepreneurship Coach 🚀

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Status](https://img.shields.io/badge/status-active-green.svg)

**An advanced multi-agent AI coaching platform for entrepreneurship education, powered by Google ADK and enhanced with real-time market intelligence.**

VentureBots revolutionizes entrepreneurship education by orchestrating specialized AI agents that guide users through the complete startup journey—from idea generation to market validation to product development. Built with Google's Agent Development Kit (ADK) and featuring a modern Chainlit interface, it provides comprehensive coaching with real-time market analysis and competitive intelligence.

## ✨ Key Features

### 🧠 **Enhanced Market Intelligence**
- **Real-time market analysis** with comprehensive competitive research
- **Multi-dimensional scoring system** evaluating feasibility, innovation, and market potential
- **Rich visual dashboards** with market insights and competitive landscapes
- **15-30 second comprehensive validation** using advanced web search capabilities

### 🤖 **AI Multi-Agent Workflow**
- **Onboarding Agent** - Personalized user experience and preference collection
- **Idea Generator** - Creative brainstorming with market-aware suggestions
- **Validator Agent** - Advanced idea validation with market intelligence
- **Product Manager** - Comprehensive PRD creation and product development guidance
- **Prompt Engineer** - AI prompt optimization and engineering assistance

### 💻 **Modern User Experience**
- **Professional Chainlit interface** optimized for conversational AI coaching
- **Real-time streaming responses** with typing indicators and smooth interactions
- **Mobile-responsive design** for learning on any device
- **Session persistence** with automatic chat history and export capabilities
- **Connection monitoring** with intelligent error handling and retry mechanisms

### 🏗️ **Enterprise-Ready Architecture**
- **Google ADK integration** for scalable multi-agent orchestration
- **FastAPI backend** with RESTful API and SSE streaming support
- **Docker containerization** for consistent deployment across environments
- **Comprehensive testing suite** with automated validation workflows

## 🏗️ System Architecture

VentureBots implements a sophisticated multi-agent architecture designed for educational excellence:

### **Core Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    Chainlit Frontend                        │
│              (Professional Chat Interface)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/SSE
┌─────────────────────▼───────────────────────────────────────┐
│                  FastAPI Backend                           │
│            (Google ADK Integration)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │      Manager Agent        │
        │   (Orchestration Layer)   │
        └─────────────┬─────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼───┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
│Onboard│  │Idea Gen   │  │Validator  │  │Product Mgr│
│Agent  │  │Agent      │  │Agent      │  │Agent      │
└───────┘  └───────────┘  └───────────┘  └───────────┘
                               │
                    ┌─────────▼─────────┐
                    │  Market Analysis  │
                    │     Tools         │
                    └───────────────────┘
```

### **Agent Responsibilities**

- **Manager Agent**: Orchestrates workflow and coordinates between specialized agents
- **Onboarding Agent**: Handles user personalization and preference collection
- **Idea Generator**: Provides creative brainstorming with market-aware suggestions
- **Validator Agent**: Conducts comprehensive market validation with real-time intelligence
- **Product Manager**: Guides PRD creation and product development strategy
- **Prompt Engineer**: Assists with AI prompt optimization and engineering

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+ (Python 3.12+ recommended)
- Git
- 8GB+ RAM (recommended for optimal performance)

### **Installation**

1. **Clone and setup**:
   ```bash
   git clone https://github.com/your-org/VentureBots.git
   cd VentureBots
   
   # Create and activate virtual environment
   python -m venv agent_venv
   source agent_venv/bin/activate    # On Windows: agent_venv\Scripts\activate
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Create a `.env` file in the project root:
   ```env
   # Required API Keys
   ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   OPENAI_API_KEY="your_openai_api_key_here"        # Optional
   SERPAPI_API_KEY="your_serpapi_api_key_here"      # Required for market research
   
   # Optional Configuration
   ADK_BACKEND_URL="http://localhost:8000"          # Backend URL for frontend
   ```

3. **API Key Setup**:
   - **[Anthropic API](https://console.anthropic.com/)**: Primary LLM provider for Claude models
   - **[SerpAPI](https://serpapi.com/)**: Powers market research and competitive analysis
   - **[OpenAI API](https://platform.openai.com/)**: Alternative LLM provider (optional)

### **Running VentureBots**

#### Option 1: Development Setup (Recommended)
```bash
# Pre-flight check (always run first)
python tests/test_imports.py

# Terminal 1: Start Backend (Port 8000)
PORT=8000 python main.py

# Terminal 2: Start Frontend (Port 8501)
source agent_venv/bin/activate
chainlit run chainlit_app.py --port 8501
```

**Access**: http://localhost:8501

#### Option 2: Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost
```

## 🎯 User Workflow

VentureBots provides a comprehensive entrepreneurship coaching journey:

### **1. Onboarding & Personalization**
- Personal profile creation with industry interests and experience level
- Learning objective setting and coaching style preferences
- Introduction to the multi-agent system and available resources

### **2. Idea Generation & Brainstorming**
- Market-aware idea generation using AI-powered creativity tools
- Opportunity identification based on current market trends
- Collaborative refinement with intelligent suggestions and alternatives

### **3. Advanced Market Validation**
- **15-30 second comprehensive validation** using real-time web search
- **Multi-dimensional scoring**: Feasibility, Innovation, Market Potential
- **Competitive landscape analysis** with detailed competitor research
- **Market size estimation** and target audience identification
- **Rich visual dashboards** presenting validation insights

### **4. Product Development Guidance**
- Comprehensive Product Requirements Document (PRD) creation
- Feature prioritization and roadmap development
- Technical architecture recommendations
- Go-to-market strategy development

### **5. Continuous Coaching & Iteration**
- Ongoing mentorship throughout the development process
- Regular check-ins and progress assessments
- Adaptive coaching based on user feedback and progress

## 🔧 API Documentation

### **Core Endpoints**

VentureBots provides a comprehensive REST API for integration and custom development:

#### **Session Management**
```bash
# Create user session
POST /apps/manager/users/{user_id}/sessions/{session_id}
Content-Type: application/json
{
  "state": {
    "initialized": true,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### **Agent Communication**
```bash
# Send message (non-streaming)
POST /run
Content-Type: application/json
{
  "app_name": "manager",
  "user_id": "user123",
  "session_id": "session456",
  "body": "Hello, VentureBots!",
  "new_message": {
    "role": "user",
    "parts": [{"text": "Hello, VentureBots!"}]
  }
}

# Send message (streaming)
POST /run_sse
Content-Type: application/json
# Same payload as above, returns Server-Sent Events
```

#### **Health & Diagnostics**
```bash
# API health check
GET /docs                    # OpenAPI documentation
GET /health                  # Service health status
```

### **Integration Examples**

#### **Python Integration**
```python
import requests

# Create session
session_response = requests.post(
    f"http://localhost:8000/apps/manager/users/{user_id}/sessions/{session_id}",
    json={"state": {"initialized": True}}
)

# Send message
response = requests.post(
    "http://localhost:8000/run",
    json={
        "app_name": "manager",
        "user_id": user_id,
        "session_id": session_id,
        "body": "Generate startup ideas for healthcare",
        "new_message": {"role": "user", "parts": [{"text": "Generate startup ideas for healthcare"}]}
    }
)
```

#### **JavaScript/Node.js Integration**
```javascript
// Using fetch API for streaming responses
const response = await fetch('http://localhost:8000/run_sse', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    app_name: 'manager',
    user_id: 'user123',
    session_id: 'session456',
    body: 'Validate my app idea',
    new_message: {
      role: 'user',
      parts: [{ text: 'Validate my app idea' }]
    }
  })
});

// Handle streaming response
const reader = response.body.getReader();
const decoder = new TextDecoder();
// Process streaming chunks...
```

## ⚠️ Troubleshooting

### **Quick Diagnostics**

#### **Pre-Flight Check** (Always run first)
```bash
python tests/test_imports.py
```

#### **Service Health Check**
```bash
# Check if services are running
lsof -i :8000  # Backend
lsof -i :8501  # Frontend

# Test backend connectivity
curl -f http://localhost:8000/docs

# Test frontend connectivity
curl -s http://localhost:8501 | head -10
```

### **Common Issues & Solutions**

#### **"No text response" from AI**
**Cause**: Import errors or backend connection issues
```bash
# Solution:
python tests/test_imports.py          # Check for import errors
PORT=8000 python main.py        # Restart backend
```

#### **Connection Refused**
**Cause**: Services not running or port conflicts
```bash
# Solution:
pkill -f "python.*main"         # Kill existing processes
PORT=8000 python main.py        # Restart with explicit port
```

#### **Import/Module Errors**
**Cause**: Incorrect import paths in sub-agents
```bash
# Solution: Ensure all sub-agents use absolute imports
# ✅ Correct: from manager.tools.tools import claude_web_search
# ❌ Wrong: from tools.tools import claude_web_search
```

#### **API Key Issues**
**Cause**: Missing or invalid API keys
```bash
# Solution:
# 1. Check .env file exists in project root
# 2. Verify API keys are valid and have sufficient credits
# 3. Restart services after updating .env
```

### **Performance Optimization**

#### **Expected Response Times**
- **First AI Response**: 10-15 seconds (model loading)
- **Subsequent Responses**: 3-8 seconds
- **Market Validation**: 15-30 seconds (comprehensive analysis)

#### **Memory Usage**
- **Backend**: ~150MB
- **Frontend**: ~100MB
- **Total System**: ~250MB

#### **Scaling Considerations**
- **Concurrent Users**: 5-10 users per instance recommended
- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: Consider Redis for session management at scale

## 📁 Project Structure

```
VentureBots/
├── main.py                         # 🚀 Backend application entry point
├── chainlit_app.py                 # 💬 Chainlit frontend interface
├── .env                            # 🔑 Environment variables & API keys
├── .env.example                    # 📋 Environment configuration template
├── requirements.txt                # 📦 Python dependencies
│
├── manager/                        # 🧠 AI Agent System
│   ├── agent.py                    # 🎯 Root orchestration agent
│   ├── config.yaml                 # ⚙️ Agent configuration
│   ├── sub_agents/                 # 🤖 Specialized coaching agents
│   │   ├── onboarding_agent/       # 👋 User onboarding & personalization
│   │   ├── idea_generator/         # 💡 Creative brainstorming agent
│   │   ├── validator_agent/        # ✅ Enhanced market validation
│   │   ├── product_manager/        # 📋 PRD creation & product guidance
│   │   └── prompt_engineer/        # 🛠️ AI prompt optimization
│   └── tools/                      # 🔧 Enhanced utilities & tools
│       ├── tools.py                # 🌐 Advanced web search & APIs
│       ├── market_analyzer.py      # 📊 Market intelligence engine
│       └── dashboard_generator.py  # 📈 Visual dashboard system
│
├── tests/                          # 🧪 Test suite
│   ├── test_imports.py             # 🔍 Import validation
│   ├── test_enhanced_analysis.py   # 📊 Market intelligence tests
│   ├── test_live_system.py         # 🔄 Live system integration
│   └── test_validator_agent.py     # ✅ Validation system tests
│
├── docs/                           # 📚 Documentation
│   ├── CLAUDE.md                   # 🤖 Development memory & guide
│   ├── DEVELOPMENT_GUIDE.md        # 💻 Developer troubleshooting
│   ├── VENTUREBOT_AGENT_ANALYSIS.md # 🔬 System architecture analysis
│   ├── chainlit.md                 # 💬 Chainlit configuration
│   └── user-testing/               # 👥 User research materials
│
├── docker/                         # 🐳 Container configuration
│   ├── Dockerfile                  # 📦 Main container
│   ├── Dockerfile.backend          # 🖥️ Backend container
│   ├── Dockerfile.frontend         # 💻 Frontend container
│   └── docker-compose.yml          # 🚀 Multi-service deployment
│
├── scripts/                        # 🛠️ Development & deployment scripts
│   ├── deploy.sh                   # 🚀 Deployment automation
│   └── health_check.sh             # 💊 Health monitoring
│
├── public/                         # 🎨 Static assets
│   ├── style.css                   # 🎨 Custom styling
│   └── agent_workflow.png          # 📊 System workflow diagram
│
└── data/                           # 💾 Runtime data (not in git)
    ├── sessions.db                 # 🗃️ Session storage
    └── logs/                       # 📝 Application logs
```

## 🐳 Docker Deployment

### **Production Deployment** (Recommended)

```bash
# Build and deploy full application
docker-compose -f docker/docker-compose.yml up --build -d

# Access application
# - Frontend: http://localhost (port 80)
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### **Development Deployment**

```bash
# Build individual containers
docker build -f docker/Dockerfile -t venturebot-app .

# Run with environment file
docker run -p 80:80 --env-file .env venturebot-app

# Run with explicit environment variables
docker run -p 80:80 \
  -e ANTHROPIC_API_KEY="your_key" \
  -e SERPAPI_API_KEY="your_key" \
  venturebot-app
```

### **Container Architecture**

- **Single Container**: Frontend + Backend (recommended for simplicity)
- **Multi-Service**: Separate containers for frontend/backend (optional)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Reverse Proxy**: Nginx for production deployments

## 🔧 Configuration

### **Agent Configuration** (`manager/config.yaml`)

```yaml
# Idea Generation Settings
num_ideas: 5                    # Ideas generated per request
max_loops: 3                    # Maximum refinement iterations
creativity_level: 0.8           # AI creativity parameter (0-1)

# Validation Settings
validation_threshold: 0.7       # Minimum score for idea approval
market_analysis_depth: "comprehensive"  # light|standard|comprehensive
competitor_analysis_limit: 10   # Maximum competitors to analyze

# Model Settings
model_provider: "anthropic"     # Primary LLM provider
model_name: "claude-3-sonnet-20240229"  # Specific model version
temperature: 0.7               # Response creativity (0-1)
max_tokens: 4000              # Maximum response length

# Performance Settings
timeout_seconds: 120           # Agent response timeout
retry_attempts: 3             # Error retry attempts
cache_enabled: true           # Response caching
```

### **Environment Variables** (`.env`)

```env
# Required API Keys
ANTHROPIC_API_KEY="sk-ant-api03-..."      # Primary LLM provider
SERPAPI_API_KEY="your-serpapi-key..."     # Market research & web search

# Optional API Keys
OPENAI_API_KEY="sk-..."                   # Alternative LLM provider
GOOGLE_API_KEY="your-google-key..."       # Google Search API (alternative)

# System Configuration
ADK_BACKEND_URL="http://localhost:8000"   # Backend URL for frontend
LOG_LEVEL="INFO"                          # Logging level
DEBUG_MODE="false"                        # Debug mode toggle

# Database Configuration
DATABASE_URL="sqlite:///./sessions.db"    # Session storage
SESSION_TIMEOUT_MINUTES=60                # Session expiration

# Performance Tuning
MAX_CONCURRENT_REQUESTS=10                # Request concurrency limit
RATE_LIMIT_REQUESTS_PER_MINUTE=60        # Rate limiting
```

## 🧪 Testing & Development

### **Test Suite Execution**

```bash
# Comprehensive test suite
python tests/test_imports.py              # Import validation
python tests/test_enhanced_analysis.py    # Market analysis testing
python tests/test_validator_agent.py      # Validator agent testing
python tests/test_live_system.py         # End-to-end system testing

# Individual agent testing
python manager/sub_agents/validator_agent/test_validator.py
python manager/sub_agents/idea_generator/test_generator.py
```

### **Development Workflow**

1. **Setup Development Environment**
   ```bash
   python -m venv agent_venv
   source agent_venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Pre-Development Checks**
   ```bash
   python tests/test_imports.py
   ```

3. **Start Development Servers**
   ```bash
   # Terminal 1: Backend
   PORT=8000 python main.py
   
   # Terminal 2: Frontend
   chainlit run chainlit_app.py --port 8501
   ```

4. **Make Changes & Test**
   ```bash
   # Test changes
   python tests/test_validator_agent.py
   
   # Full system test
   python tests/test_live_system.py
   ```

### **Adding New Agents**

1. **Create Agent Directory**
   ```bash
   mkdir manager/sub_agents/your_agent
   touch manager/sub_agents/your_agent/agent.py
   touch manager/sub_agents/your_agent/__init__.py
   ```

2. **Implement Agent Class**
   ```python
   from google.adk.agents import Agent
   
   class YourAgent(Agent):
       async def handle(self, conversation, memory):
           # Your agent implementation
           pass
   ```

3. **Register Agent in Manager**
   ```python
   # In manager/agent.py
   from manager.sub_agents.your_agent.agent import YourAgent
   ```

4. **Add Tests**
   ```python
   # Create test_your_agent.py
   # Add unit tests for your agent
   ```

## 🤝 Contributing

We welcome contributions to VentureBots! Here's how to get started:

### **Development Setup**

1. **Fork & Clone**
   ```bash
   git clone https://github.com/your-username/VentureBots.git
   cd VentureBots
   ```

2. **Setup Environment**
   ```bash
   python -m venv agent_venv
   source agent_venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### **Development Guidelines**

- **Code Style**: Follow PEP 8 with 88-character line length
- **Testing**: Add tests for new features and bug fixes
- **Documentation**: Update relevant documentation
- **Import Paths**: Use absolute imports (`from manager.tools.tools import`)

### **Pull Request Process**

1. **Ensure Tests Pass**
   ```bash
   python tests/test_imports.py
   python tests/test_live_system.py
   ```

2. **Update Documentation**
   - Update README.md if needed
   - Add docstrings to new functions
   - Update API documentation

3. **Submit PR**
   - Clear description of changes
   - Link to related issues
   - Request review from maintainers

## 📚 Resources & References

### **Technical Documentation**
- [Google Agent Development Kit (ADK)](https://github.com/google/agent-developer-kit)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Chainlit Documentation](https://docs.chainlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### **Educational Resources**
- [Entrepreneurship Coaching Best Practices](https://www.coursera.org/learn/entrepreneurship)
- [AI Agent Design Patterns](https://arxiv.org/abs/2308.11432)
- [Market Validation Methodologies](https://www.ycombinator.com/library/6h-how-to-build-your-seed-deck)

### **Community & Support**
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Wiki**: Comprehensive documentation and guides

---

**🚀 Ready to revolutionize entrepreneurship education with AI?**

Start your journey with VentureBots today and experience the future of AI-powered coaching for startup success!
