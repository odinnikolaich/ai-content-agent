# ADR-003: Weak-PC / Local-First Design

## Context
Target hardware is Intel Celeron N5095 with 16 GB RAM and no assumed high-end GPU.

## Decision
Keep orchestration lightweight, make heavy generation optional, require mock mode, and isolate rendering/generation behind replaceable interfaces.

## Consequences
The repository remains testable locally and can later attach local or remote generation providers without architectural changes.
