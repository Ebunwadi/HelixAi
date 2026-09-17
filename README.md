# HelixAI

Multi-tenant agentic customer operations platform.

This repository is a monorepo. The system design report is the product and architecture source of truth. Architecture Decision Records live in [`docs/adr`](docs/adr).

## Repository layout

```text
apps/api      Python FastAPI application
apps/web      Next.js + TypeScript frontend
packages/     Shared AI/application libraries (introduced in later sprints)
infrastructure/
docs/adr      Architecture Decision Records
scripts/      Repository-level checks
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

On Windows PowerShell use `Copy-Item` instead of `cp` if needed.

### Prepare the API and database

```bash
cd apps/api
uv sync --group dev
uv run alembic upgrade head
uv run helix-bootstrap-dev
uv run uvicorn helix_api.main:app --reload --host 0.0.0.0 --port 8000
```

The bootstrap command is local-only and creates a deterministic development user/tenant plus sample Acme and Globex customers. It prints the same subject and tenant identifiers used by `apps/web/.env.example`.

### Run the web app

```bash
cd apps/web
npm ci
npm run dev
```

Open http://localhost:3000. The protected shell first calls `GET /api/v1/me`; application navigation is rendered only after the API establishes a valid tenant context.

## Sprint 2 authentication model

Authentication and application tenancy are intentionally separate:

1. An external identity proves who the caller is. In production mode the API validates a Bearer JWT using issuer, audience and JWKS settings.
2. `User.external_identity_id` maps that identity to an internal HelixAI user.
3. A tenant selection is authorised through an active `Membership` row.
4. Services receive the trusted current context, and repositories still filter tenant-owned data by `tenant_id`.

For local development, `HELIX_AUTH_MODE=dev` accepts explicit `X-Helix-*` headers. Do not use that mode as production authentication.

## Sprint 2 API routes

```text
GET  /health
GET  /api/v1/me
GET  /api/v1/tenants/current
GET  /api/v1/customers
GET  /api/v1/customers/{id}
POST /api/v1/conversations
GET  /api/v1/conversations
```

Messages and model calls deliberately start in Sprint 3.

## Checks

From `apps/api`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Database integration tests run in CI with PostgreSQL after `alembic upgrade head`.

From `apps/web`:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Or run the local repository checks with `scripts/check.sh` / `scripts/check.ps1`. The GitHub Actions API job additionally validates the real migration and cross-tenant integration test.

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
