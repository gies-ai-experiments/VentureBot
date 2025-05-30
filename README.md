# AgentLab

This project demonstrates a multi-stage agent pipeline using the Google Agent Developer Kit (ADK). The pipeline:
1. Brainstorms ideas
2. Validates each idea in parallel
3. Selects the best idea
4. Iterates to improve quality
5. Generates a final self-contained AI prompt

## Prerequisites
- Python 3.8+
- git
- An OpenAI API key (for the `LiteLlm` model)

## Setup
1. Clone this repository and navigate into it:
   ```bash
   git clone <repo-url>
   cd <repo-directory>
   ```
2. Create and activate a virtual environment called `agent_venv`:
   ```bash
   python3 -m venv agent_venv
   source agent_venv/bin/activate    # On Windows use: agent_venv\Scripts\activate
   ```
3. Upgrade pip (optional but recommended):
   ```bash
   pip install --upgrade pip
   ```
4. Install required packages:
   ```bash
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
```
Open your browser at `http://localhost:8080` to interact with the pipeline.

### Command-Line Run
```bash
# Navigate to the agentlab_v5 directory
cd agentlab_v5

# Run the agent pipeline in the terminal
adk run
```  

## Troubleshooting
- Ensure the virtual environment is activated when running commands.
- Confirm `adk`, `python`, and `pip` point to the `agent_venv` binaries (`which adk`).
- Install missing dependencies if you encounter import errors.
- Make sure you're in the `agentlab_v5` directory when running the agent.

## References
- ADK documentation: https://github.com/google/agent-developer-kit
