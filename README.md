# HelixAI

Multi-tenant agentic customer operations platform.

This repository is a monorepo. The system design report is the product and architecture source of truth. Architecture Decision Records live in [`docs/adr`](docs/adr), and sprint implementation notes live in [`docs/sprints`](docs/sprints).

## Repository layout

```text
apps/api      Python FastAPI application
apps/web      Next.js + TypeScript frontend
packages/     Shared AI/application libraries (introduced in later sprints)
infrastructure/
docs/adr      Architecture Decision Records
docs/sprints  Sprint implementation notes
scripts/      Repository-level developer checks
```

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Node.js 24 and npm
- Docker Desktop

## Local setup

```bash
git clone https://github.com/Ebunwadi/HelixAi.git
cd HelixAi
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
docker compose up -d
```

On Windows PowerShell use `Copy-Item` instead of `cp`.

### Prepare the API and database

```bash
cd apps/api
uv sync --group dev
uv run alembic upgrade head
uv run helix-bootstrap-dev
uv run uvicorn helix_api.main:app --reload --host 0.0.0.0 --port 8000
```

The bootstrap command creates a deterministic local user/tenant plus sample Acme and Globex customers.

### Run the web app

```bash
cd apps/web
npm ci
npm run dev
```

Open http://localhost:3000.

## Authentication and tenancy

Authentication and application tenancy are separate:

1. An external identity proves who the caller is.
2. `User.external_identity_id` maps that identity to an internal HelixAI user.
3. A tenant selection is authorised through an active `Membership`.
4. Services receive a trusted `CurrentContext`, and tenant-owned repositories still filter by `tenant_id`.

For local development, `HELIX_AUTH_MODE=dev` accepts explicit `X-Helix-*` headers. Production mode validates a Bearer JWT.

## Sprint 3 model configuration

Sprint 3 deliberately uses direct model calls before LangChain, LangGraph, tools, RAG or agents.

Local development defaults to the deterministic mock provider:

```text
HELIX_MODEL_PROVIDER=mock
```

The mock provider makes no Azure call. To use Azure OpenAI, configure `apps/api/.env`:

```text
HELIX_MODEL_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=YOUR-DEPLOYMENT-NAME
```

Never commit the real API key.

The Azure implementation uses the Azure OpenAI v1 Responses API through the standard OpenAI Python client. Application services depend on HelixAI's provider-independent `ModelGateway`, not directly on SDK types.

## Current API routes

```text
GET  /health
GET  /api/v1/me
GET  /api/v1/tenants/current
GET  /api/v1/customers
GET  /api/v1/customers/{id}

POST /api/v1/conversations
GET  /api/v1/conversations
GET  /api/v1/conversations/{id}/messages
POST /api/v1/conversations/{id}/messages
POST /api/v1/conversations/{id}/messages/stream

POST /api/v1/ai/interpret-investigation
```

The streaming endpoint returns Server-Sent Events:

```text
message.created
token.delta
message.completed
error
```

Assistant messages store model name, provider response ID, input/output token counts and latency alongside the generated text.

## Checks

From `apps/api`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

CI also starts PostgreSQL, applies all Alembic migrations and enables the database integration tests.

From `apps/web`:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Or run the repository checks with `scripts/check.sh` / `scripts/check.ps1`.

## Configuration conventions

- API configuration: `apps/api/.env.example` → local `apps/api/.env`.
- Browser configuration: `apps/web/.env.example` → local `apps/web/.env.local`.
- Production credentials and model/API secrets belong in a secret store, never in Git.
- Development Docker credentials in example configuration are non-secret local defaults.

## Contribution workflow

1. Work on a sprint/feature branch; do not push features directly to `main`.
2. Use conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
3. Keep changes tied to a GitHub issue where practical.
4. Run lint, type checks, tests and builds before review.
5. Update an ADR in the same PR when an architectural decision changes.
6. Merge only after GitHub Actions is green.

Project board: [HelixAI Development](https://github.com/users/Ebunwadi/projects/4).
