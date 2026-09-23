# Configuration

## Precedence
1. Explicit CLI/programmatic overrides
2. Environment variables
3. config/default.yaml
4. Built-in defaults

PHASE 1 is provider-agnostic. Mock is the default and no API key or network access is required.

## Supported settings
.env.example documents runtime mode, logging, paths, Russian 9:16 video defaults, 43–60 second duration bounds, reliability/QC settings, and provider names.

## Validation
Log levels, timeouts, retry counts, video dimensions/FPS, and QC dimensions/durations are validated at load time. Paths use pathlib.Path for Windows compatibility.

## Testing
```bash
python -m pytest
```

The full application CLI and automatic .env loading are intentionally deferred until the corresponding later phase.
