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
cp .env.example .env
```

On Windows PowerShell, copy the env file with:

```powershell
Copy-Item .env.example .env
```

`.env` is gitignored. Put local values there; never commit secrets.

### API

```bash
cd apps/api
uv sync --group dev
uv run helix-api
```

The API listens on http://localhost:8000. Check http://localhost:8000/health.

### Web

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000.

### PostgreSQL

```bash
docker compose up -d
```

Default connection string (also in `.env.example`):

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
```

Auto-fix frontend lint with `npm run format`.

Or run everything from the repo root:

```bash
bash scripts/check.sh
```

```powershell
powershell -File scripts/check.ps1
```

## Configuration conventions

- Keys belong in `.env.example` with empty or non-secret local defaults.
- Real values belong only in `.env` or a secret store.
- Application code must not commit API keys, connection strings with passwords, or model credentials.
- Azure / Foundry variables are listed in `.env.example` for later sprints; they can stay empty now.

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
