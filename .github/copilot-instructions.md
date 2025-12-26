# Trio Coordination Rules
This document defines the roles and operational workflows for AI Agents (specifically GitHub Copilot and Claude) collaborating on the VentureBot project.

🤖 Agent Roles & Specializations
🏎️ GitHub Copilot
Focus: High-level oversight and general development.
Responsibilities:
General issue resolution and feature scaffolding.
High-level architectural changes and project structure maintenance.
Handling boilerplate code and routine updates.
Initial documentation and README updates.

🧠 Claude
Focus: Highly technical and deep-logic implementation.
Responsibilities:
Solving complex algorithmic challenges and performance bottlenecks.
Deep debugging of intermittent or subtle logical errors.
Refactoring core services (Orchestrator, Gateway) for better scalability.
Implementing sophisticated prompt engineering and AI model integrations.

🛠️ Mandatory Operational Workflow
All agents must follow this strict multi-phase process for every issue or feature request.

1. Planning Phase 📝
Before writing a single line of implementation code, the agent must: 1. Analyze the issue thoroughly. 2. Draft a Formal Implementation Plan detailing: * Affected files and components. * Proposed logic changes. * Potential edge cases or risks. * Verification steps (tests to run).

2. Approval Phase ✅
The plan MUST be presented to the Human Developer. * Wait for explicit approval before proceeding. * Incorporate any feedback or constraints provided by the human during this phase.

3. Implementation Phase 💻
Once the plan is approved: * Execute the changes as outlined in the plan. * Maintain the project's coding standards. * Verify the changes locally (e.g., build checks, linting, or tests).

4. Pull Request (PR) Phase 🚀
Agents are empowered and encouraged to create their own Pull Requests (from time to time).
The PR description must link to the original plan and summarize the implementation results.
5. Final Review & Merge 🤝
Crucial Rule: The Human Developer always retains the authority to merge code.
Agents should never attempt to merge their own PRs into the primary branch.

🏗️ Repository Guidelines (Summary)
Detailed guidelines available in the original repository documentation.

Project Structure
services/: Backend services (FastAPI, Orchestrator, Tools).
crewai-agents/: CrewAI blueprints and configs.
frontend/: React + Vite SPA (TypeScript).
Key Commands
Backend: python -m uvicorn services.api_gateway.app.main:app --reload
Frontend: npm run dev in frontend/
Full Stack: docker compose up --build
