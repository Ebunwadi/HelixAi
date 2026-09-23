# HelixAI

Multi-tenant agentic customer operations platform.

This repository is a monorepo. Architecture Decision Records live in docs/adr and sprint implementation notes live in docs/sprints.

## Local setup

Prerequisites: Python 3.12, uv, Node.js 24/npm, and Docker Desktop.

1. Copy apps/api/.env.example to apps/api/.env.
2. Copy apps/web/.env.example to apps/web/.env.local.
3. Run docker compose up -d.
4. In apps/api run uv sync --group dev, uv run alembic upgrade head, then uv run helix-bootstrap-dev.
5. Start the API with uv run uvicorn helix_api.main:app --reload --host 0.0.0.0 --port 8001.
6. In apps/web run npm ci and npm run dev.

The API is available at http://localhost:8001 and Swagger UI at http://localhost:8001/docs.

## Sprint 4 baseline RAG

Local development uses cloud-free defaults:

HELIX_EMBEDDING_PROVIDER=mock
HELIX_RAG_STORAGE_PROVIDER=local
HELIX_RAG_SEARCH_PROVIDER=local

Original uploads and the local derived vector index are written under apps/api/.helix/ and are gitignored.

Supported baseline document types are UTF-8 .txt, .md, and text-based .pdf files. Image-only/scanned PDFs require OCR and are intentionally outside Sprint 4.

The baseline pipeline is:

upload -> original storage -> text extraction -> chunking -> embeddings -> vector index

question -> query embedding -> vector retrieval -> numbered evidence -> model generation -> answer + citations

To use Azure-backed providers, switch the matching provider settings and configure:

AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_EMBEDDING_DEPLOYMENT
AZURE_STORAGE_CONNECTION_STRING
AZURE_STORAGE_CONTAINER
AZURE_AI_SEARCH_ENDPOINT
AZURE_AI_SEARCH_API_KEY
AZURE_AI_SEARCH_INDEX

HELIX_EMBEDDING_DIMENSIONS must match the embedding output size and the Azure AI Search vector field dimension.

## Knowledge API routes

POST /api/v1/knowledge-bases
GET  /api/v1/knowledge-bases
POST /api/v1/knowledge-bases/{id}/documents
GET  /api/v1/knowledge-bases/{id}/documents
POST /api/v1/knowledge-bases/{id}/search
POST /api/v1/knowledge-bases/{id}/answer

The search route exposes retrieval results directly. The answer route performs explicit retrieve-then-generate RAG and returns citations separately from the generated answer.

## Checks

API:
- uv run ruff check .
- uv run ruff format --check .
- uv run pyright
- uv run pytest

Web:
- npm run lint
- npm run typecheck
- npm test
- npm run build

CI also starts PostgreSQL and applies all Alembic migrations before database integration tests.

## Configuration and contribution

- API configuration: apps/api/.env.example -> apps/api/.env.
- Browser configuration: apps/web/.env.example -> apps/web/.env.local.
- Never commit production credentials or model/API secrets.
- Work on feature/sprint branches and merge only after CI is green.
- Update an ADR when a material architectural decision changes.

Project board: https://github.com/users/Ebunwadi/projects/4
