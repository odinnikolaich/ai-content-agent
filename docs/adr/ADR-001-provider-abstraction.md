# ADR-001: Provider Abstraction

## Context
AI services may change, may require payment, and may be unavailable locally.

## Decision
Agents use provider interfaces. Concrete local, remote and mock providers are infrastructure implementations.

## Consequences
The pipeline can be tested without external services and providers can be replaced without rewriting agent business logic.
