# Testing Strategy

## Unit

Test domain validation, agent transformations, prompt construction and state transition rules with no network access.

## Provider

Test provider adapters against mocks/fakes. Real provider tests are opt-in and never required for CI.

## Integration

Run the orchestrator with all mock providers from CREATED to COMPLETED without API keys or network access.

## Validation

Inspect synthetic media and verify duration, dimensions, FPS, codecs and audio presence.

## End-to-end

Verify the complete mock pipeline and checkpoint/resume behavior.

The target mock command is conceptually:

```
content-agent create --topic "Строительство модульного дома зимой" --duration 50 --language ru --mock
```

Tests must remain practical on a Celeron N5095 / 16 GB RAM machine.
