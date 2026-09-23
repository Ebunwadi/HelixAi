# Architecture Decision Records

This directory records material HelixAI design choices.

Each ADR should stay short and explicit: context, decision, and consequences. When implementation reveals a better choice, amend the relevant ADR rather than silently changing direction.

| ADR | Decision |
| --- | --- |
| [ADR-001](001-python-fastapi-backend.md) | Python + FastAPI for the primary backend |
| [ADR-002](002-modular-monolith.md) | Start as a modular monolith |
| [ADR-003](003-postgresql-source-of-truth.md) | PostgreSQL as transactional source of truth |
| [ADR-004](004-azure-ai-search.md) | Azure AI Search for knowledge retrieval |
| [ADR-005](005-langgraph-after-manual-foundations.md) | LangGraph after manual agent foundations |
| [ADR-006](006-approval-for-sensitive-side-effects.md) | Approval required for sensitive side effects |
| [ADR-007](007-sse-before-websockets.md) | SSE before WebSockets |
| [ADR-008](008-azure-container-apps.md) | Azure Container Apps initially |
| [ADR-009](009-version-and-evaluate-prompts.md) | Version prompts and evaluate changes |
| [ADR-010](010-fine-tune-after-baseline.md) | Fine-tuning only after a measured baseline |
| [ADR-011](011-separate-identity-and-tenant-authorization.md) | Separate external identity from HelixAI tenant authorisation |
| [ADR-012](012-direct-responses-api-behind-model-gateway.md) | Direct Responses API behind a provider-independent model gateway |
| [ADR-013](013-search-index-is-derived-data.md) | Treat the search index as derived data |
