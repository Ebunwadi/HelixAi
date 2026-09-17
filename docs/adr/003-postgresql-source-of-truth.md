# ADR-003: Use PostgreSQL as the transactional source of truth

## Status

Accepted

## Context

HelixAI has a relational domain: tenants, users, memberships, customers, conversations, agent runs, approvals and audit events. These records need transactions, constraints and tenant-scoped queries. Search indexes and vector stores are derived representations, not authoritative business state.

## Decision

Use PostgreSQL as the transactional source of truth. The ORM choice (SQLAlchemy 2.x vs SQLModel) is deferred to Sprint 2 and will be recorded in a follow-up ADR.

## Consequences

- Application writes go to PostgreSQL first.
- Azure AI Search, blobs and caches may be rebuilt from PostgreSQL plus source documents.
- Local development includes PostgreSQL via Docker Compose.
