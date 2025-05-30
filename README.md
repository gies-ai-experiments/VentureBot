# AgentLab

A multi-agent framework for idea generation, validation, and product development using Google's Agent Development Kit (ADK) and generative AI models.

## Project Overview

AgentLab is a sophisticated framework that orchestrates multiple AI agents to collaborate on complex tasks including idea generation, validation, competitive analysis, and Product Requirements Document (PRD) creation. The system supports both web-based and command-line interfaces, with evolution through multiple versions (v1-v4) that incrementally add capabilities and refinements.

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

## Running the Agent
The ADK CLI provides both a web UI and a CLI runner.

### Web UI
```bash
# Navigate to the agentlab_v5 directory
cd agentlab_v5

# Start the interactive web interface
adk web
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

## Usage

### Web Interface (Recommended)

Start the interactive web interface using the main FastAPI application:

```bash
python main.py
```

Then open your browser at `http://localhost:80` to access the ADK web interface.

### Command Line Interface

You can also run individual agent versions directly:

**Latest version (v5)**:
```bash
python agentlab_v5/agent.py
```

**Previous versions**:
```bash
python agentlab_v4/agent.py  # Includes ux fixes
python agentlab_v3/agent.py  # Includes competitor search
python agentlab_v2/agent.py  # Enhanced multi-agent workflow  
python agentlab_v1/agent.py  # Basic implementation
```

### Using Google ADK CLI

If you have the ADK CLI installed globally:

```bash
# Navigate to the agentlab_v5 directory
cd agentlab_v5

# Run the agent pipeline in the terminal in the agentlab_v5 directory
=======
# Web interface
adk web

# Command line runner
adk run
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
├── main.py                 # FastAPI application entry point
├── agents/                 # Modular agent implementations
│   ├── idea_coach_agent.py
│   ├── validation_agent.py
│   ├── product_manager_agent.py
│   ├── orchestrator_agent.py
│   └── test_*.py          # Unit tests for agents
├── agentlab_v1/           # Version 1: Basic implementation
├── agentlab_v2/           # Version 2: Enhanced workflow
├── agentlab_v3/           # Version 3: Added competitor search
├── agentlab_v4/           # Version 4: Latest with improved UX
├── agentlab_v5/           # Version 5: Fixed agent orchestration issue
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
└── README.md            # This file
```

## Configuration

Each agent version includes a `config.yaml` file for customization:

- `num_ideas`: Number of ideas to generate per iteration
- `max_loops`: Maximum refinement iterations
- `validation_thresholds`: Criteria for idea validation
- `model_settings`: LLM model configuration

Example configuration:
```yaml
num_ideas: 5
max_loops: 3
validation_threshold: 0.7
model_provider: "anthropic"
```

## Docker Deployment

Build and run the containerized version:

```bash
# Build the Docker image
docker build -t agentlab .

# Run the container
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
- Ensure the virtual environment is activated when running commands.
- Confirm `adk`, `python`, and `pip` point to the `agent_venv` binaries (`which adk`).
- Install missing dependencies if you encounter import errors.
- Make sure you're in the `agentlab_v5` directory when running the agent.

### Common Issues

**Import Errors**: Ensure virtual environment is activated and dependencies are installed:
```bash
which python  # Should point to agent_venv
pip install -r requirements.txt
```

**API Key Issues**: Verify your `.env` file contains valid API keys and is in the project root.

**Port Conflicts**: If port 80 is in use, modify the port in `main.py` or set the `PORT` environment variable.

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

## References

- [Google Agent Development Kit (ADK)](https://github.com/google/agent-developer-kit)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)