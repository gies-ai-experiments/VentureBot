# CLAUDE.md

AI-powered venture ideation assistant with staged journey flow.

> See [AGENTS.md](./AGENTS.md) for coding style, testing, and commit guidelines.

## Project Overview

- **Purpose**: Guide users through venture ideation using AI agents (CrewAI + FastAPI + React)
- **Type**: code
- **Stack**: Python backend (FastAPI), React frontend (Vite/TypeScript), CrewAI agents, Docker

## Architecture

```
services/
├── api_gateway/app/     # FastAPI gateway
├── orchestrator/        # Journey flow orchestration
└── tools/               # Shared utilities

crewai-agents/src/venturebot_crew/config/
├── agents.yaml          # Agent definitions
└── tasks.yaml           # Task configurations

frontend/                # React + Vite SPA
```

## Key Commands

```bash
# Backend
python -m uvicorn services.api_gateway.app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Full stack (Docker)
docker compose up --build
```

## Sync Points

When modifying stages/agents:
1. Update `services/orchestrator/flows/staged_journey_flow.py`
2. Update stage list in `frontend/src/App.tsx`
3. Update agent configs in `crewai-agents/src/venturebot_crew/config/`

## Current Focus
- [ ] [Update during /session-start]

## Roadmap
- [ ] [Add planned features]

## Session Log
### 2025-12-27
- Initial CLAUDE.md created with roadmap sections
- Next: Define current development priorities
