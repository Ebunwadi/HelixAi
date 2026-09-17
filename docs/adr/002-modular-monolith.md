# ADR-002: Start as a modular monolith

## Status

Accepted

## Context

The frontend, API and AI runtime will change together frequently. Splitting into microservices or many repositories on day one adds multiple PRs, version coordination, harder local setup and duplicated CI without a demonstrated scaling need.

## Decision

Keep HelixAI in one git repository and deploy the API initially as a modular monolith. Domain modules, the agent runtime, retrieval and background work keep clear internal boundaries so they can be extracted later if workload or ownership requires it.

## Consequences

- `apps/web`, `apps/api` and later `apps/worker` share one repository.
- Cross-module calls stay in-process until an ADR records a split.
- Distributed-system complexity is deferred until there is a concrete reason.
