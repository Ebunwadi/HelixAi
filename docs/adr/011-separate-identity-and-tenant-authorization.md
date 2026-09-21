# ADR-011: Separate external identity from HelixAI tenant authorisation

## Context

A valid identity-provider token proves who a caller is, but it does not by itself define which HelixAI workspace the caller may access. HelixAI is multi-tenant and a user may eventually belong to more than one workspace with different roles.

## Decision

External authentication resolves a stable identity first. HelixAI then maps that identity to an internal user and requires an active `Membership` for the requested tenant before creating the trusted `CurrentContext`.

Tenant-owned repositories continue to include `tenant_id` in their queries as defence in depth.

## Consequences

- A client-supplied tenant ID is only a requested workspace, not an authority grant.
- Identity-provider tenancy and HelixAI application tenancy remain separate concepts.
- Future AI tools inherit a trusted tenant context instead of accepting tenant identity from model arguments.
