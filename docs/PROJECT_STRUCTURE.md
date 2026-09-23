# Project Structure

Planned structure:

```
ai-content-agent/
├── src/
│   ├── core/
│   │   ├── models.py
│   │   ├── interfaces.py
│   │   ├── exceptions.py
│   │   ├── config/
│   │   └── logging/
│   ├── agents/
│   │   ├── research/
│   │   ├── ideas/
│   │   ├── script/
│   │   ├── scenes/
│   │   ├── visuals/
│   │   ├── voice/
│   │   ├── captions/
│   │   └── quality/
│   ├── pipeline/
│   │   ├── orchestrator/
│   │   ├── state/
│   │   ├── checkpoints/
│   │   └── recovery/
│   └── infrastructure/
│       ├── providers/
│       ├── media/
│       └── rendering/
├── remotion/
├── prompts/
├── projects/
├── tests/
├── docs/
└── config/
```

Directories are introduced only when implementation work requires them; documentation does not imply that every module is already implemented.
