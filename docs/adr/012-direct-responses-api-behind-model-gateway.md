# ADR-012: Use the Responses API behind a HelixAI model gateway

## Context

Sprint 3 is intended to teach raw LLM application fundamentals before agent frameworks. Azure OpenAI's current v1 API is compatible with the standard OpenAI client and exposes the Responses API. HelixAI also needs tests and local development to work without cloud credentials.

## Decision

HelixAI calls the Responses API directly through a small provider-independent `ModelGateway` interface.

Two implementations exist in Sprint 3:

- `OpenAIResponsesGateway` for an Azure OpenAI v1 endpoint.
- `MockModelGateway` for deterministic local development and CI.

LangChain and LangGraph are deliberately not introduced yet.

HelixAI persists its own conversation messages in PostgreSQL and requests `store=False` from the model provider.

## Consequences

- Application services depend on HelixAI model types rather than SDK types.
- The provider can be replaced or mocked without rewriting conversation logic.
- We can inspect messages, structured outputs, tokens, latency and streaming before introducing orchestration frameworks.
- Provider-specific advanced features must be added deliberately instead of leaking throughout the application.
