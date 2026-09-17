# ADR-009: Version prompts and evaluate changes

## Status

Accepted

## Context

Prompts change production behaviour. Unversioned multi-line strings in application code make it hard to know which prompt produced a run, or to prevent quality regressions.

## Decision

Treat prompts as versioned, reviewable configuration. Each agent run records the prompt version used. Material prompt, model or retrieval changes require evaluation against a baseline before promotion in production-like environments.

## Consequences

- Prompts live under versioned files (later `packages/prompts` / `apps/api` prompt modules).
- Anonymous in-code prompts are rejected as the production pattern.
- CI will later fail on critical eval regressions, not only unit tests.
