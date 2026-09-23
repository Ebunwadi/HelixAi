# Sprint 4 — Knowledge & Baseline RAG

## Goal

Build the first explicit retrieval-augmented generation pipeline without agent or orchestration frameworks.

## Scope

- Tenant-scoped knowledge bases.
- Original document storage.
- .txt, .md and text-based .pdf extraction.
- Baseline overlapping character chunking.
- Mock and Azure OpenAI embedding providers.
- Local derived vector index and Azure AI Search adapter.
- Vector retrieval with tenant and knowledge-base filters.
- Grounded answer generation from retrieved passages.
- Application citations containing document/chunk provenance.
- Knowledge UI for upload, indexing, retrieval and answer inspection.

## Explicit non-goals

- OCR for scanned/image-only PDFs.
- Semantic reranking, hybrid search, query rewriting or retrieval fusion.
- Background ingestion workers and retry queues.
- Agent tools or autonomous retrieval decisions.
- LangChain/LangGraph.
- Production-scale document ingestion.

## Baseline pipeline

upload -> original storage -> text extraction -> chunking -> embeddings -> vector index

question -> query embedding -> vector retrieval -> numbered evidence -> model generation -> answer + citations

## Learning outcome

The implementation should make chunking, embeddings, vector similarity, indexing, retrieval context and grounded generation visible enough to explain without relying on a RAG framework abstraction.
