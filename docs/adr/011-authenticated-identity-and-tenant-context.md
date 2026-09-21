# ADR-011: Separate external identity from HelixAI tenant authorisation

## Status

Accepted

## Context

HelixAI will use an enterprise identity provider in production, but identity-provider tenancy and application tenancy are different concepts. A valid external token proves who a user is; it does not by itself prove which HelixAI workspace data that user may access. Trusting a tenant identifier supplied by the browser, token text or future model output without checking application membership would create a cross-tenant data-leak risk.

Local development also needs a way to exercise protected routes without requiring an Azure app registration for every contributor.

## Decision

- Production authentication uses a signed Bearer JWT validated for issuer, audience, expiry and signature through the provider's JWKS endpoint.
- The token subject maps to `User.external_identity_id`.
- The requested HelixAI tenant is accepted only after an active `Membership` row authorises that user for that tenant.
- Business services receive a trusted `CurrentContext`; repository queries still include `tenant_id` as defence in depth.
- `HELIX_AUTH_MODE=dev` enables explicit `X-Helix-*` headers for local development only. It is an adapter, not a production authentication mechanism.

## Consequences

- Switching or configuring the external identity provider does not change domain-service tenant rules.
- A valid token cannot access another tenant merely by changing a request header.
- Future agents/tools inherit tenant context from the authenticated runtime rather than from model-generated arguments.
- Deployment must prevent dev-auth mode outside approved local/development environments.
