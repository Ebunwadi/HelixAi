# ADR-010: Fine-tune only after a measured baseline

## Status

Accepted

## Context

Fine-tuning is often used too early, before prompt and RAG quality are measured. Tenant knowledge also changes faster than model weights should be retrained. RAG is the correct path for current organisational facts.

## Decision

Establish a prompt/RAG baseline first. Fine-tuning is a later, controlled experiment (ticket classification/routing) and is adopted only if it beats the baseline on accuracy, latency, cost and operational complexity.

## Consequences

- Sprint 3–9 improve prompting, retrieval and evaluation before any fine-tune.
- Private/current knowledge stays in RAG, not in fine-tuned weights.
- The baseline path is retained unless the candidate clearly wins the intended objective.
