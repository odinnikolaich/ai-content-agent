# Provider Architecture

Core interfaces:

- LLMProvider
- ImageProvider
- VideoProvider
- VoiceProvider
- TranscriptionProvider
- StorageProvider
- MediaInspector
- Renderer

Provider policy:

- Mock providers are mandatory for testability.
- Local providers are optional implementations for free/local execution where hardware permits.
- Remote providers are optional adapters.
- Paid services are never mandatory project dependencies.
- Agents depend on interfaces, not vendor implementations.

Examples of future implementations may include local or remote models, but the architecture does not select a vendor at PHASE 0.
