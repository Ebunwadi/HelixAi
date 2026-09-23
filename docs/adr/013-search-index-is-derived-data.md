# ADR-013: Treat the search index as derived data

## Context

RAG needs fast retrieval over chunked and embedded document content. Azure AI Search is the production retrieval engine, but HelixAI also needs clear ownership boundaries and a cloud-free local workflow.

## Decision

PostgreSQL owns knowledge-base, document and chunk metadata. Original uploaded bytes are stored in document storage. The vector search index is treated as a derived projection that can be rebuilt from owned content.

RAG infrastructure is accessed through HelixAI interfaces for document storage, embeddings and search. Sprint 4 provides local implementations plus Azure Blob Storage, Azure OpenAI embeddings and Azure AI Search adapters.

## Consequences

- Search-index loss does not redefine which documents HelixAI owns.
- Local development and CI can run without Azure credentials.
- Tenant and knowledge-base filters are applied at retrieval time.
- Ingestion currently coordinates database and external index writes synchronously; later resilience work must address retries and partial failures explicitly.
