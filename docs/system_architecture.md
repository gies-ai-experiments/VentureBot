# VentureBots System Architecture

This document captures the target end-state architecture for the VentureBots AI entrepreneurship coaching platform and highlights the near-term MVP scope. It aligns the technical direction across teams and provides the baseline for ADRs, scaffolding, and implementation work.

## 1. High-Level View

- **User Interface:** `frontend/` hosts a React + Vite SPA (TypeScript) that renders the coaching UI, message timeline, and incremental UI extensions (dashboards, analytics) in future releases. The SPA communicates with the backend via HTTPS for REST calls and WebSockets for streaming responses.
- **API Gateway:** `services/api-gateway/` contains a FastAPI service that terminates TLS, handles OIDC-based authentication when enabled, enforces request validation and rate limiting, and brokers chat traffic between the SPA and the orchestrator. Long-running jobs are deferred to the async queue.
- **Orchestrator:** `services/orchestrator/` embeds the CrewAI runtime. It manages crews, agent lifecycles, task routing, guardrails (timeouts, retries, safety policies), and structured execution plans defined in `configs/`.
- **Agent Services:** `services/agents/<domain>/` house specialized agent packages (e.g., `market_research`, `financial_modeling`, `coaching_assistant`). Each exposes CrewAI-compatible abilities, consumes shared SDKs from `libs/agents/`, and integrates with tool adapters in `libs/integrations/`.
- **Data Layer:** `services/data-api/` provides domain APIs over PostgreSQL (and eventually GraphQL). Vector search is exposed via a dedicated microservice (e.g., Weaviate) in `services/vector-search/`. Analytics data targets a columnar store (BigQuery/ClickHouse).
- **Async & Batch:** `infrastructure/queue/` manages Kafka or RabbitMQ for agent events, analytics, email, and experiment triggers. Background workers live in `services/workers/` and consume from the queue for asynchronous workloads.
- **Observability & Control Plane:** `infrastructure/observability/` contains OpenTelemetry collectors, centralized logging (Loki), metrics (Prometheus), alerting, and feature flag configuration. An admin UI surfaces operational insights.
- **Shared Libraries:** `libs/` offers reusable adapters for LLM providers, integrations (CRM, calendaring, payments), caching, telemetry, and configuration.
- **Documentation & Testing:** `docs/` stores ADRs, runbooks, and architecture assets. `tests/` contains integration suites, contract tests, and cross-service scenarios.

## 2. Component Responsibilities

### Frontend (`frontend/`)
- React/Vite SPA with modular feature slices, shared UI kit, and integration tests.
- Establishes WebSocket sessions to stream agent responses with typing indicators.
- Integrates with the API gateway via a generated API client and typed DTOs.

### API Gateway (`services/api-gateway/`)
- FastAPI layer responsible for authentication, request validation, session tokens, and rate limiting.
- Provides REST endpoints for session management and WebSocket endpoints for live chat.
- Dispatches agent requests to the orchestrator and enqueues long-running jobs to the message bus.

### Orchestrator (`services/orchestrator/`)
- CrewAI runtime organized into `crews/`, `agents/`, `tasks/`, `pipelines/`, `policies/`, and `runtime/`.
- Uses typed task specifications defined in `domain/` and structured configurations in `configs/`.
- Applies guardrails such as concurrency caps, timeout policies, safety filters, and structured output validation.

### Agent Services (`services/agents/`)
- Self-contained packages per business function.
- Each agent inherits from shared base classes in `libs/agents/`, registers tools, and references prompts/templates stored in `prompts/`.
- Includes domain-specific tests to guarantee deterministic behaviour against mocked tool outputs.

### Tooling & Integrations (`libs/integrations/`)
- Adapters for LLM providers, vector stores, CRM, calendaring, payment APIs, and future integrations.
- Provides caching wrappers, rate limiting utilities, and unified error handling.

### Data Services
- **Relational Storage:** PostgreSQL schemas segmented per service (e.g., `public`, `orchestrator`, `analytics`) to store users, ventures, session records, and agent outputs.
- **Vector Search:** Dedicated microservice (Weaviate or Pinecone) with versioned collections per venture/project for embeddings.
- **Analytics:** Columnar datastore (BigQuery/ClickHouse) to ingest event logs, funnel metrics, and experiment results.
- **Document Store:** Optional MongoDB/DynamoDB for semi-structured transcripts and replay snapshots.
- **Logging Storage:** S3-compatible buckets for raw traces, attachments, and archival data.

### Async & Batch Execution
- Kafka/RabbitMQ topics in `infrastructure/queue/` distribute agent events, analytics payloads, email notifications, and experiment triggers.
- Worker pools in `services/workers/` (Celery or Dramatiq) process background tasks, respecting concurrency limits and retry policies.
- Temporal or Airflow schedulers orchestrate recurring coaching programs and experiment automation.

### Observability & Control Plane
- OpenTelemetry instrumentation propagates traces from the gateway through orchestrator and agent services.
- Structured JSON logs with correlation IDs feed Loki/ELK pipelines.
- Prometheus/Grafana dashboards expose latency, success rates, token consumption, queue depth, and error budgets.
- Feature flag service provides controlled rollouts and experiment toggles.

### Security & Governance
- OAuth2/OIDC at the gateway, JWT validation, and service-to-service mTLS (SPIFFE IDs).
- Secrets stored in Vault or cloud secret managers with sidecar injection; short-lived access tokens enforced platform-wide.
- Policy enforcement via OPA (Open Policy Agent) for agent tool governance and data access control.
- Compliance posture includes audit logging, PII encryption at rest, vulnerability scanning (Snyk/Trivy), and regular key rotation.

## 3. Data Flows

1. **Chat Interaction**
   - User sends a message from the SPA → API gateway validates session → orchestrator selects appropriate crew → crew delegates tasks to domain agents → agent responses stream back over WebSockets → message history persists via the data API.
2. **Long-Running Tasks**
   - Gateway enqueues task on the message bus → workers execute asynchronously (e.g., deep market research) → results stored via data API → gateway notifies frontend through WebSocket events or polling.
3. **Analytics Pipeline**
   - Orchestrator and agents emit structured events → queue forwards to analytics workers → events land in columnar store → dashboards surface insights.

## 4. Development & Deployment Lifecycle

- **Containerization:** Every service ships with a Dockerfile using multi-stage builds and pinned base images. `docker-compose.yml` (and overrides) orchestrate the local stack.
- **CI/CD:** GitHub Actions workflows cover linting, type checks (MyPy), unit/integration tests, Docker builds, and automated deploys via Argo CD or Cloud Deploy.
- **Environments:** Dev supports ephemeral preview stacks per feature branch. Staging mirrors production with anonymized data. Production uses blue/green rollouts and smoke tests.
- **Infrastructure-as-Code:** Terraform provisions VPC networking, databases, caches, queues, storage, and secret managers. Helm charts deliver Kubernetes deployment manifests. Secrets stay in Vault or cloud-specific managers; sealed secrets enable GitOps automation.
- **Local Tooling:** `make` or `just` commands bootstrap services, populate `.env.example` files, and seed fixtures for demos.

## 5. Caching & Performance

- Redis cluster stores session tokens, short-lived agent context, rate limiting counters, and crew run state; Redis Streams offer lightweight event distribution.
- In-process caches (e.g., `functools.lru_cache`) memoize prompt templates and config artifacts; invalidation propagates via pub/sub.
- Managed ingress (NGINX/Envoy) delivers load balancing with sticky sessions for WebSockets.
- Preloading prompts/tools warms agent contexts; queue backpressure safeguards upstream LLM quotas.

## 6. MVP Scope (Current Milestone)

The MVP showcases an end-to-end chat experience without the full production footprint:

- **Frontend:** Minimal React/Vite SPA implementing a chat UI (message list, composer, typing indicator). No authentication, dashboards, or analytics.
- **API Gateway:** FastAPI service exposing REST + WebSocket endpoints. Handles chat session persistence, forwards messages to the orchestrator, and manages basic SQLite-backed storage.
- **Orchestrator:** CrewAI-powered service that simulates agent execution (e.g., echo/baseline LLM responses) with lightweight policies.
- **Persistence:** SQLite database for chat sessions and message history; no external data services or vector stores yet.
- **Deployment:** Docker Compose definitions for the three services; `docker-compose up` should launch the entire stack without missing environment variables. Telemetry, feature flags, and third-party integrations are intentionally excluded.
- **Validation:** Ensure stable WebSocket communication, message persistence, and graceful error handling before expanding scope.

## 7. Roadmap & Next Steps

1. Draft ADRs covering the service decomposition, data stores, and CrewAI governance policies.
2. Scaffold repository structure to match the architecture (services, libs, configs, infrastructure).
3. Provision core infrastructure (PostgreSQL, Redis, message queue, vector database) and baseline CI/CD workflows.
4. Implement the orchestrator skeleton with CrewAI best practices, guardrails, and typed task specifications.
5. Incrementally migrate existing logic into modular agent services with comprehensive tests.

This architecture will evolve alongside ADRs and implementation feedback. Revisit and update this document as services are scaffolded, integrations mature, and non-functional requirements shift.

