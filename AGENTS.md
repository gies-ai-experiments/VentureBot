# Repository Guidelines

## Project Structure & Module Organization
- `services/`: Python backend (FastAPI gateway in `services/api_gateway/app/`, orchestration in `services/orchestrator/`, shared tools in `services/tools/`)
- `crewai-agents/`: CrewAI blueprint + prompt/task configs (`crewai-agents/src/venturebot_crew/config/*.yaml`)
- `frontend/`: React + Vite SPA (TypeScript) and nginx container for production builds
- `docs/`, `scripts/`, `data/`: architecture notes, ops scripts, local runtime data (SQLite/logs)

## Build, Test, and Development Commands
- Backend setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run backend (dev): `python -m uvicorn services.api_gateway.app.main:app --reload --port 8000` (docs: `http://localhost:8000/docs`)
- Frontend setup: `cd frontend && npm ci`
- Run frontend (dev): `cd frontend && npm run dev` (set `VITE_API_BASE_URL=http://localhost:8000` if needed)
- Lint/build frontend: `cd frontend && npm run lint` / `npm run build`
- Run full stack (Docker): `docker compose up --build` (frontend: `http://localhost`, backend: `http://localhost:8000`)

## Coding Style & Naming Conventions
- Python: 4-space indent, type hints where practical, `snake_case` for functions/modules, `PascalCase` for classes.
- TypeScript/React: prefer functional components, `PascalCase` components, keep API URL configurable (see `frontend/src/App.tsx`).
- Keep request/response models in `services/api_gateway/app/schemas.py` and persistence in `services/api_gateway/app/models.py`.

## Testing Guidelines
- Backend testing uses `pytest` (listed in `requirements.txt`). Add tests under `tests/` as `test_*.py` and run `pytest`.
- Smoke check: `curl http://localhost:8000/healthz` and a simple chat session via `POST /api/chat/sessions`.
- Frontend has no unit test runner configured; use `npm run build` as a sanity check.

## Commit & Pull Request Guidelines
- Commit subjects commonly use prefixes like `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`; keep the subject short and imperative.
- PRs should include: what changed + why, steps to verify, and screenshots for UI changes.
- Never commit secrets. Use `.env.template` as a starting point for local `.env`.

## Agent/Stage Changes
- If you add/change journey stages, keep `services/orchestrator/flows/staged_journey_flow.py` mappings and the stage list in `frontend/src/App.tsx` in sync.
- When editing prompts/tasks, update `crewai-agents/src/venturebot_crew/config/agents.yaml` and `crewai-agents/src/venturebot_crew/config/tasks.yaml`; ensure keys match the orchestrator’s task names.
