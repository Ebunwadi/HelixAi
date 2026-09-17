# ADR-005: Use LangGraph after manual agent foundations

## Status

Accepted

## Context

Agent frameworks hide model calls, tool loops and state. HelixAI is also a learning programme: we need to understand messages, structured output, tool calling and a manual agent loop before introducing graph orchestration.

## Decision

Do not introduce LangGraph until a manual tool-call loop exists (Sprint 6). LangGraph is adopted in Sprint 7 for stateful graphs, checkpoints, retries and human interruption. LangChain is used selectively for integrations, not as the application architecture.

## Consequences

- Early sprints call models through our own adapter.
- Domain logic stays framework-neutral behind interfaces.
- Framework churn is contained; swapping orchestration later does not rewrite business services.
