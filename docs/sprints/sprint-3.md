# Sprint 3 — LLM Fundamentals

## Goal

Add HelixAI's first model-backed behaviour without LangChain, LangGraph, tools, RAG or agents.

## Scope

- Provider-independent model gateway.
- Azure OpenAI v1 Responses API adapter.
- Deterministic mock provider for local development and CI.
- System/user/assistant message handling.
- Persisted conversation messages.
- Model metadata: provider response ID, model name, input/output tokens and latency.
- Structured output with a Pydantic-backed investigation intent schema.
- Server-Sent Events for token streaming.
- AI Workspace UI for chat and structured intent inspection.

## Explicit non-goals

- Tool calling.
- Autonomous loops.
- RAG or embeddings.
- LangChain/LangGraph.
- Long-term memory.
- Provider-side conversation storage.

## Learning outcome

By the end of the sprint, the implementation should make it possible to explain the full path from a browser message to model input, model response, streamed deltas, token metadata and PostgreSQL persistence without relying on an orchestration framework.
