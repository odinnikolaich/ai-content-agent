# Provider Architecture

Core provider/infrastructure interfaces are defined in `src/core/interfaces.py`.

## Interfaces

- `LLMProvider`
- `ImageProvider`
- `VideoProvider`
- `VisualProvider`
- `VoiceProvider`
- `TranscriptionProvider`
- `StorageProvider`
- `MediaInspector`
- `Renderer`
- `ResearchProvider`
- `CaptionRenderer`

## Policy

- Mock providers are mandatory for end-to-end testing.
- Local providers are optional and should be selected according to available hardware.
- Remote providers are optional adapters.
- Paid services are never mandatory project dependencies.
- Agents depend on protocols/interfaces, not vendor implementations.
- No vendor SDK is imported by the domain model layer.
- Provider-specific parameters are carried only through provider request contracts.

The architecture intentionally does not select OpenAI, ElevenLabs, Runway,
LongCat, or another vendor at PHASE 0.1. Concrete providers are a later
implementation decision.
