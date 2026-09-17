# ADR-007: Use SSE before WebSockets

## Status

Accepted

## Context

Agent runs can take seconds or longer. The UI needs incremental progress (stage changes, tool activity, token deltas, approval required). Communication is predominantly server-to-client during a run.

## Decision

Stream agent output with Server-Sent Events (SSE) initially. WebSockets are an alternative only if later bidirectional real-time requirements justify them.

## Consequences

- `GET /api/v1/agent-runs/{id}/stream` is the first streaming contract.
- Clients can reconnect; authoritative run state remains available via REST.
- Event payloads must not leak raw chain-of-thought or secrets.
