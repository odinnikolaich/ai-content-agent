# Dependency Rules

Allowed direction:

```
interfaces / entry points
        ↓
application agents + pipeline
        ↓
core domain contracts
        ↑
infrastructure adapters implement core interfaces
```

More concretely:

- Domain models must not import providers, HTTP clients, FFmpeg or Remotion.
- Agents may depend on core models and provider interfaces only.
- Agents must not import concrete providers.
- Agents must not mutate orchestrator state.
- Pipeline may call agents and interfaces, but provider implementations remain behind adapters.
- QualityAgent depends on a MediaInspector interface, not FFmpeg directly.
- Remotion is an infrastructure/rendering adapter, not a domain dependency.
- UI/API/CLI layers may invoke application services but must not contain business logic.
- Concrete providers may depend on external SDKs/libraries.
