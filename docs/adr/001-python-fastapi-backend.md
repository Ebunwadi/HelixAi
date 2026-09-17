# ADR-001: Use Python + FastAPI for the primary backend

## Status

Accepted

## Context

HelixAI is an AI-native SaaS product. The backend must support typed async APIs, structured validation, and a Python-first AI ecosystem (model clients, later LangGraph, evaluation tooling). Node.js and .NET are capable alternatives, but they are a weaker fit for the target AI engineering skill path.

## Decision

Use Python 3.12+ and FastAPI as the primary backend. Pydantic will validate request, response and tool-argument schemas.

## Consequences

- Backend work lives in `apps/api` and follows Python packaging, testing and typing conventions.
- We accept the operational cost of maintaining a Python toolchain alongside the TypeScript frontend.
- Node.js/.NET backends are rejected for the MVP unless a later ADR justifies a split.
