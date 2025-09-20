# VentureBots Development Guide

This document captures the essentials for working on the CrewAI-powered VentureBot stack after the migration away from Google ADK.

## 🔩 Core Components

```
VentureBot/
├── main.py                 # FastAPI backend exposing /api/sessions and /api/chat
├── chainlit_app.py         # Chainlit UI that calls the REST API
├── manager/
│   ├── config.yaml         # Model and workflow configuration
│   ├── agent.py            # Convenience module exporting `venturebot_service`
│   ├── service.py          # High-level facade used by FastAPI/Chainlit
│   └── crew/
│       ├── agents.py       # CrewAI agent factory
│       ├── schemas.py      # Pydantic models for structured task output
│       ├── state.py        # Session state dataclasses
│       └── workflow.py     # VentureBotCrew orchestrating the multi-agent flow
└── tests/
    └── test_imports.py     # Mocked end-to-end diagnostic
```

## ⚙️ Environment Setup

1. **Create / activate a virtual environment**
   ```bash
   python -m venv agent_venv
   source agent_venv/bin/activate
   ```

2. **Install backend dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   Create a `.env` file in the repository root:
   ```env
   GEMINI_API_KEY="your-google-gemini-key"
   OPENAI_API_KEY="optional-openai-key"
   ANTHROPIC_API_KEY="optional-claude-key"
   ```
   CrewAI uses the first available key in the order listed above.

## 🚀 Running the Stack

### Backend (FastAPI)
```bash
PORT=8000 python main.py
```
This exposes:
- `POST /api/sessions` – initialise a session and receive the welcome message
- `POST /api/chat` – send user messages and receive VentureBot responses
- `GET /health` – readiness probe

### Frontend (Chainlit)
```bash
chainlit run chainlit_app.py --port 8501
```
The Chainlit client streams characters from the REST responses to emulate live typing.

## ✅ Testing

The test suite uses monkeypatched CrewAI calls so it runs without hitting real LLMs.

```bash
pytest            # Run all tests
pytest tests/test_imports.py  # Run the diagnostic only
```

If `pytest` is not installed globally, it is provided via `requirements.txt`.

## 🛠️ Troubleshooting

| Issue | Fix |
|-------|-----|
| `ValueError: Missing API key` | Ensure `.env` defines `GEMINI_API_KEY` (or another provider key) before starting the backend. |
| Chainlit displays “Session not ready” | Confirm the FastAPI server is running on `http://localhost:8000` and reachable from the frontend. |
| Test failures referencing CrewAI | Reinstall dependencies with `pip install -r requirements.txt`; CrewAI must be v0.193.0 or later. |
| Want to inspect session state | Call `service.snapshot(session_id)` from a REPL (see `manager/service.py`). |

## 📎 Developer Tips

- The orchestrator logic lives in `manager/crew/workflow.py`. When changing the flow, update the Pydantic response models in `schemas.py` simultaneously.
- Keep prompts inside task descriptions rather than embedding imperative logic in agents; `_execute_task` already enforces JSON outputs.
- The Chainlit client intentionally streams responses character-by-character. Adjust the delay in `VentureBotSession.stream_message` if you want faster or slower typing.
- Run `pytest -q` after major changes to ensure the mocked happy-path still succeeds.

Happy shipping! 🚀
