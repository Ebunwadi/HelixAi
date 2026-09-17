# ADR-008: Use Azure Container Apps initially

## Status

Accepted

## Context

Production-style deployment needs containers for the web app, API and workers. AKS provides more orchestration control but adds cluster administration the project does not initially need.

## Decision

Deploy to Azure Container Apps. AKS is reserved for a later, justified evolution if custom scheduling, networking or Kubernetes-specific features are required.

## Consequences

- Infrastructure targets Container Apps, not AKS, in Sprint 12.
- Local development uses Docker Compose rather than a local Kubernetes stack.
- Workers can scale with queued workload without operating a cluster.
