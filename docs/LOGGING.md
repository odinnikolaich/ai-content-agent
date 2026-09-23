# Logging

Use structured logs. Each event should be able to carry project_id, pipeline state, agent/stage, provider, duration_ms, retry_count and error metadata.

Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.

Logging must never expose API keys, tokens or sensitive request content by default.
