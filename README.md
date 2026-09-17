# HelixAI

Multi-tenant agentic customer operations platform.

This repository is a monorepo. The system design report is the product and architecture source of truth. Architecture Decision Records live in [`docs/adr`](docs/adr).

## Repository layout

```text
apps/api      Python API (uv + FastAPI)
apps/web      Next.js + TypeScript frontend
packages/     Shared libraries (empty in Sprint 1)
infrastructure/
docs/adr      Architecture Decision Records
scripts/
```

Sprint 1 does **not** require Azure or OpenAI access.

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or the official installer)
- Node.js 24 and npm
- Docker Desktop (for PostgreSQL)

## First-time setup

```bash
git clone https://github.com/Ebunwadi/HelixAi.git
cd HelixAi
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

On Windows PowerShell:

```powershell
Copy-Item apps/api/.env.example apps/api/.env
Copy-Item apps/web/.env.example apps/web/.env.local
```

The local environment files are gitignored. Put real local values there; never commit secrets.

### API

```bash
cd apps/api
uv sync --group dev
uv run uvicorn helix_api.main:app --reload --host 0.0.0.0 --port 8000
```

The API listens on http://localhost:8000. Check http://localhost:8000/health.

`uv run helix-api` is also available as a non-reloading startup command. Auto reload is deliberately kept in the development command rather than hard-coded into application startup.

### Web

```bash
cd apps/web
npm ci
npm run dev
```

Open http://localhost:3000.

### PostgreSQL

```bash
docker compose up -d
```

Default local connection string (also in `apps/api/.env.example`):

```text
postgresql+asyncpg://helix:helix@localhost:5432/helix
```

The API does not use the database yet. Compose is in place so Sprint 2 can add migrations without rediscovering local infrastructure.

## Checks

From `apps/api`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Format Python with `uv run ruff format .`.

From `apps/web`:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Auto-fix supported frontend lint issues with `npm run lint:fix`.

The Sprint 1 frontend test is intentionally only a repository smoke test. Real component and end-to-end tests are added as application behaviour is introduced in later sprints.

Or run all documented checks from the repo root:

```bash
bash scripts/check.sh
```

```powershell
powershell -File scripts/check.ps1
```

## Configuration conventions

- API configuration is documented in `apps/api/.env.example`; local values belong in `apps/api/.env`.
- Browser/web configuration is documented in `apps/web/.env.example`; local values belong in `apps/web/.env.local`.
- Real production credentials and model/API secrets belong in a secret store, never in Git.
- Non-secret local development defaults, such as the Docker Compose PostgreSQL username/password, may be documented in example files.
- Azure / Foundry variables are listed for later sprints and can stay empty now.

## Contribution workflow

1. Create a branch from the current sprint branch (do not push directly to `main`).
2. Use conventional commits:
   - `feat:` new behaviour
   - `fix:` a bug
   - `test:` tests only
   - `docs:` documentation
   - `chore:` tooling, repo or CI
3. Keep changes reviewable and tied to a GitHub issue (`HAI-xxx`).
4. Run the checks above before opening a pull request.
5. If the change alters architecture, update `docs/adr` in the same PR.
6. GitHub Actions must pass on the PR.

Project board: [HelixAI Development](https://github.com/users/Ebunwadi/projects/4).

## Sprint 1 status

The runnable skeleton is the FastAPI `/health` endpoint plus the default Next.js app. Domain features (auth, tenancy, RAG, agents) start in later sprints.
