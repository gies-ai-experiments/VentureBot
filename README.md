# VentureBots — AI Entrepreneurship Coach

VentureBots is a stage-based, multi-agent entrepreneurship coaching app powered by CrewAI. It ships as a FastAPI backend (REST + WebSockets) with a React + Vite frontend.

## Architecture (MVP)
- `frontend/` (React/Vite) connects to the backend via WebSocket streaming (`/api/chat/ws/...`) and REST (`/api/...`).
- `services/api_gateway/` is the FastAPI gateway (sessions, message persistence, websocket events).
- `services/orchestrator/` runs the stage-by-stage journey and calls the CrewAI blueprint in `crewai-agents/`.
- Runtime state is stored in SQLite under `data/` (default: `data/chat.sqlite3`).

## Quick Start (Docker)
1. Create `.env` from the template:
   ```bash
   cp .env.template .env
   ```
2. Set at least `OPENAI_API_KEY` in `.env` (used by the CrewAI LLM + the web-search tool).
3. Run the stack:
   ```bash
   docker compose up --build
   ```
4. Open:
   - Frontend: `http://localhost`
   - Backend docs: `http://localhost:8000/docs`
   - Health: `http://localhost:8000/healthz`

## Local Development

### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.template .env
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm ci
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## API (Gateway)
- `POST /api/chat/sessions` creates a session (`auto_start` can run onboarding immediately).
- `POST /api/chat/sessions/{session_id}/messages` stores a user message and returns the assistant reply.
- `GET /api/chat/sessions/{session_id}/messages` returns persisted history.
- `WS /api/chat/ws/{session_id}` streams events (`assistant_token`, `assistant_message`, `stage_update`, etc.).

## Editing Agents and Stages
- Agent/task prompts live in `crewai-agents/src/venturebot_crew/config/agents.yaml` and `crewai-agents/src/venturebot_crew/config/tasks.yaml`.
- The stage progression and task mappings live in `services/orchestrator/flows/staged_journey_flow.py`.
- The UI stage labels live in `frontend/src/App.tsx` (`JOURNEY_STAGES`).

## Project Structure
```
.
├── services/                      # FastAPI gateway + orchestrator + tools
├── crewai-agents/                 # CrewAI blueprint (agents/tasks YAML)
├── frontend/                      # React/Vite SPA + nginx production container
├── docs/                          # Architecture notes
├── data/                          # SQLite DB + backend logs (local/runtime)
├── docker-compose.yml             # Local/prod compose entrypoint
└── AGENTS.md                      # Contributor guide
```

## Deployment
`main` deploys via GitHub Actions (`.github/workflows/deploy.yml`) to a VM using `docker compose`. Vercel/Chainlit deployments are not used.

## Contributing
See `AGENTS.md`.
