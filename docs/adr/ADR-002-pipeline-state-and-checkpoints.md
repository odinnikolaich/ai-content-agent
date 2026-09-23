# ADR-002: Explicit Pipeline State and Checkpoints

## Context
Video generation is multi-stage and may fail or be interrupted.

## Decision
The orchestrator owns explicit state transitions and persists a checkpoint after each successful stage.

## Consequences
Runs can be resumed and failures can be diagnosed without regenerating completed stages.
