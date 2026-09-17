# ADR-004: Use Azure AI Search for knowledge retrieval

## Status

Accepted

## Context

HelixAI needs lexical, vector and hybrid retrieval with metadata filters for tenant-scoped knowledge. pgvector and specialist vector databases are viable, but the learning and portfolio target is Azure AI Search, including hybrid search with Reciprocal Rank Fusion.

## Decision

Use Azure AI Search as the knowledge retrieval system. Retrieval strategy (keyword, vector, hybrid, reranking) will be benchmarked rather than assumed.

## Consequences

- Document chunks are indexed into Azure AI Search, not treated as the system of record.
- Local/dev work may use adapters until Azure resources exist; the application talks to a retrieval interface, not a vendor SDK everywhere.
- pgvector remains an alternative if a later ADR justifies it.
