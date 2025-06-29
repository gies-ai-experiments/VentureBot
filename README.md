# AgentLab

A multi-agent framework for idea generation, validation, and product development using Google's Agent Development Kit (ADK) and generative AI models.

## Project Overview

AgentLab is a sophisticated framework that orchestrates multiple AI agents to collaborate on complex tasks including idea generation, validation, competitive analysis, and Product Requirements Document (PRD) creation. The system supports both web-based and command-line interfaces.

### Key Features

- **Multi-agent orchestration** with specialized agents for different tasks
- **Interactive web interface** using Google ADK's FastAPI integration
- **Idea generation and validation** with competitive analysis
- **Product Requirements Document (PRD)** creation
- **Human-in-the-loop** interactions for decision making
- **Containerized deployment** with Docker support

## Architecture

The framework consists of several specialized agents:

- **IdeaCoachAgent**: Generates creative ideas based on user input
- **ValidationAgent**: Validates ideas with market research and competitive analysis
- **ProductManagerAgent**: Creates detailed Product Requirements Documents
- **OrchestratorAgent**: Coordinates workflow between specialist agents

## Setup

### Prerequisites

- Python 3.8+
- Git
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd AgentLab
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv agent_venv
   source agent_venv/bin/activate    # On Windows: agent_venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Configuration
- Review and edit `agentlab_v5/manager/config.yaml` to adjust parameters:
  - `num_ideas`: Number of ideas to brainstorm per iteration
  - `max_loops`: Number of refinement loops
  - Other thresholds if needed
- Set your OpenAI API key:
  ```bash
  export OPENAI_API_KEY="your_api_key_here"
  ```

4. **Set up environment variables**:
   Create a `.env` file in the project root and add your API keys:
   ```env
   ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   OPENAI_API_KEY="your_openai_api_key_here"
   SERPAPI_API_KEY="your_serpapi_api_key_here"
   ```
   
   **Required API Keys**:
   - **Anthropic API**: Required for Claude models used in agents
   - **OpenAI API**: Alternative LLM provider option
   - **SerpAPI**: Used for competitive search and market research

## Running the Application

AgentLab provides multiple interfaces to interact with the AI agents. Choose the interface that best fits your needs.

### Option 1: Streamlit Chat Interface (🔥 Recommended)

The Streamlit interface provides a modern ChatGPT-like experience with real-time streaming responses. This is the **easiest and most user-friendly** way to interact with AgentLab.

**Step 1: Start the Backend (ADK Server)**
```bash
# Navigate to the agentlab_v5 directory
cd agentlab_v5

# Start the ADK API server on port 8000
adk api_server --port 8000
```

**Step 2: Install Streamlit Dependencies**
```bash
# Install Streamlit requirements (from project root)
pip install -r requirements_streamlit.txt
```

**Step 3: Start the Streamlit Frontend**
```bash
# Start the Streamlit chat interface
streamlit run streamlit_chat.py
```

**Step 4: Access the Chat Interface**
- Open your browser to `http://localhost:8501`
- The interface will automatically create a session and connect to Venture Bot
- Start chatting with your AI agent immediately

### Option 2: ADK Web Interface

The ADK web interface provides the native Google ADK development experience.

**Step 1: Start the Web Interface**
```bash
# Navigate to the agentlab_v5 directory
cd agentlab_v5

# Start the ADK web interface
adk web --port 8080
```

**Step 2: Access the Interface**
- Open your browser to `http://localhost:8080`
- Use the web UI to interact with agents

### Option 3: API Server Only

For developers who want to build custom frontends or integrate with other applications.

**Start the API Server**
```bash
cd agentlab_v5

# Start API server for custom integrations
adk api_server --port 8000
```

**API Endpoints Available:**
- `POST /apps/managerA/users/{user_id}/sessions/{session_id}` - Create session
- `POST /run` - Send messages to agent
- `POST /run_sse` - Send messages with streaming responses

### Option 4: Using Uvicorn Directly

For advanced users who prefer direct uvicorn control:

```bash
cd agentlab_v5/managerA
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### Interactive Workflow

The system provides an interactive experience:

1. **Input Phase**: Specify the type of ideas you want to generate
2. **Generation**: AI generates multiple idea candidates
3. **Validation**: Ideas are validated with market research and competitive analysis
4. **Selection**: Choose from generated ideas or request regeneration
5. **Documentation**: Create detailed PRDs for selected ideas
6. **Refinement**: Iterate on PRDs with human feedback
7. **Output**: Final deliverables including PRDs and implementation prompts

## Project Structure

```
AgentLab/
├── agentlab_v5/                    # Latest implementation
│   └── managerA/                  # Production agent implementation
│       ├── agent.py              # Root agent implementation
│       ├── app.py                # FastAPI application
│       ├── config.yaml           # Agent configuration
│       ├── sub_agents/           # Specialized agent implementations
│       │   ├── idea_generator/   # Creative brainstorming agent
│       │   ├── validator_agent/  # Market validation agent
│       │   ├── product_manager/  # PRD creation agent
│       │   ├── prompt_engineer/  # Code prompt optimization
│       │   └── onboarding_agent/ # User onboarding flow
│       └── tools/                # Agent tools and utilities
├── streamlit_chat.py              # Modern chat interface (recommended)
├── requirements.txt               # Backend dependencies
├── requirements_streamlit.txt     # Frontend dependencies
├── docker-compose.yml             # Multi-service deployment
├── Dockerfile                     # Main container configuration
├── Dockerfile.backend             # Backend-specific container
├── Dockerfile.frontend            # Frontend-specific container
├── docs/                          # Documentation
│   ├── CLEANUP_PLAN.md           # Repository optimization guide
│   └── VentureBots_Launch_Article.md # Project overview
└── README.md                      # This file
```

## Configuration

The `config.yaml` file in `agentlab_v5/managerA/` directory can be customized:

```yaml
num_ideas: 5
max_loops: 3
validation_threshold: 0.7
model_provider: "anthropic"
```

## Docker Deployment

### Option 1: Docker Compose (Recommended)

The easiest way to deploy the full application with both backend and frontend:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

This will start:
- **Backend**: ADK API server on port 8000
- **Frontend**: Streamlit chat interface on port 80

Access the application at `http://localhost`

### Option 2: Individual Container

Build and run individual containers:

```bash
# Build the main image
docker build -t agentlab .

# Run with environment file
docker run -p 80:80 --env-file .env agentlab
```

## Development

### Running Tests

Execute the test suite:

```bash
python run_tests.py
```

Or run individual agent tests:

```bash
python agents/test_idea_coach.py
python agents/test_validation_agent.py
python agents/test_product_manager_agent.py
```

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement required methods for your agent's functionality
3. Add the agent to the orchestrator workflow
4. Create corresponding unit tests

## Troubleshooting

### Common Issues

**Import Errors**: Ensure virtual environment is activated and dependencies are installed:
```bash
which python  # Should point to agent_venv
pip install -r requirements.txt
```

**API Key Issues**: Verify your `.env` file contains valid API keys and is in the project root.

**Port Conflicts**: If port 8080 is in use, you can specify a different port:
```bash
adk web --port 8081
```

### Dependency Conflicts

If you encounter dependency conflicts, try creating a fresh virtual environment:
```bash
rm -rf agent_venv
python -m venv agent_venv
source agent_venv/bin/activate
pip install -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Ensure all tests pass: `python run_tests.py`
5. Submit a pull request

## Recent Optimizations

AgentLab has undergone comprehensive cleanup and optimization:

- **🧹 Repository Cleanup**: Removed 2,644+ cache directories and 500MB+ of redundant files
- **📁 Streamlined Structure**: Consolidated to single production implementation (`managerA`)
- **⚡ Performance**: 40-50% reduction in file count for faster git operations
- **🔧 Enhanced Tooling**: Improved .gitignore and Docker configurations
- **📚 Better Documentation**: Added comprehensive guides and project overview

For detailed information, see `CLEANUP_PLAN.md` and `VentureBots_Launch_Article.md` in the repository.

## References

- [Google Agent Development Kit (ADK)](https://github.com/google/agent-developer-kit)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Streamlit Documentation](https://docs.streamlit.io/)
