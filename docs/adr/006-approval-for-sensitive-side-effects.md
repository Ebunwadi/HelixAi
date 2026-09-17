# ADR-006: Require approval for sensitive side effects

## Status

Accepted

## Context

Agents can request tools. Read-only investigation is useful; unattended external actions (email, financial or destructive operations) are not acceptable for the MVP. Human-in-the-loop is a production control, not a UI flourish.

## Decision

Classify tools by policy. Read-only and draft-only tools may run automatically. External communication requires human approval. Financial/destructive actions are out of MVP. The model cannot bypass the policy engine.

## Consequences

- Sensitive tool execution pauses the run, creates an `ApprovalRequest`, and resumes only after approve/reject/expiry.
- Approval state is persisted so a restarted process can continue correctly.
- Fully autonomous external actions are rejected for the MVP.
