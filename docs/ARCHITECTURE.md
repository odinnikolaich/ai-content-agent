# Architecture

## Goal

ai-content-agent is a local-first, provider-agnostic pipeline for producing short social videos from a user request. The application must remain usable without mandatory paid APIs and must support a mock mode for end-to-end testing.

## Layers

1. **Domain/Core** — immutable domain models, contracts, interfaces, errors and configuration abstractions. No infrastructure dependencies.
2. **Agents/Application** — use cases that transform typed domain inputs into typed domain outputs. Agents depend on core contracts, never concrete providers.
3. **Pipeline** — orchestration, state transitions, checkpoints, retries, recovery and caching.
4. **Infrastructure/Providers** — concrete LLM, image, video, voice, transcription, storage and media-inspection implementations.
5. **Rendering** — Remotion and FFmpeg adapters isolated from business logic.
6. **Interfaces** — future CLI/API/UI entry points.

## Data flow

User request → validation → research → ideas → concept → script → scene plan → visual assets → voice → transcription/captions → timeline → render → quality control → final video.

## Design principles

- Typed contracts between stages.
- Provider abstraction; no vendor-specific imports in agents.
- Immutable/versioned stage outputs where practical.
- Checkpoint after successful stages.
- Deterministic cache keys including prompt version.
- Mock mode must run without network access or API keys.
- Heavy generation is optional and replaceable; the orchestration layer must remain lightweight for an Intel Celeron N5095 / 16 GB RAM machine.
