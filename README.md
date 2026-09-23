# AI Content Agent

Local-first, provider-agnostic pipeline for producing short social videos.

## Status
**PHASE 1 — Core Foundation**

Includes PHASE 0.1 immutable/versioned contracts plus YAML/environment configuration, structured JSON logging, cross-platform workspace management, serialization helpers, and unit tests.

## Principles
- Provider-agnostic
- Immutable contracts
- Mock-first and free to test
- Designed for Intel Celeron N5095 / 16 GB RAM
- Checkpointable architecture

## Installation
```bash
python -m venv .venv
```
Windows:
```bat
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Testing
```bash
python -m pytest
```

## Roadmap
PHASE 0 → PHASE 0.1 → PHASE 1 → PHASE 2 Pipeline/State/Checkpoints → PHASE 3 Mock Providers → PHASE 4 Agents → PHASE 5 Remotion → PHASE 6 Voice/Captions → PHASE 7 QC → PHASE 8 CLI → PHASE 9 API → PHASE 10 Real Providers → PHASE 11 UI → PHASE 12 Optimization

## License
MIT
