# Module Contracts

PHASE 0.1 defines explicit, immutable stage-boundary contracts. The domain
layer does not import provider SDKs, HTTP clients, FFmpeg, Remotion, or UI code.

## Domain contracts

- `ContentRequest`
- `ResearchResult`
- `ResearchSource`
- `ContentIdea`
- `SelectedConcept`
- `Script`
- `ScriptSegment`
- `ScenePlan`
- `Scene`
- `VisualGenerationRequest`
- `MediaAsset`
- `VoiceAsset`
- `Transcript`
- `TranscriptSegment`
- `CaptionTrack`
- `Caption`
- `Timeline`
- `RenderJob`
- `MediaMetadata`
- `QualityReport`
- `FinalVideo`
- `CacheKey`

All contracts are immutable. A new stage result is a new value; agents must not
mutate a previous stage output in place.

## Stage boundaries

| Stage | Input | Output |
|---|---|---|
| Validation | ContentRequest | validated ContentRequest |
| Research | ContentRequest | ResearchResult |
| Ideas | ContentRequest + ResearchResult | list[ContentIdea] |
| Concept selection | list[ContentIdea] | SelectedConcept |
| Script | ContentRequest + SelectedConcept | Script |
| Scene planning | Script | ScenePlan |
| Visual generation | VisualGenerationRequest | MediaAsset |
| Voice generation | text/voice request | VoiceAsset |
| Transcription | VoiceAsset | Transcript |
| Captions | Transcript + timeline context | CaptionTrack |
| Timeline | ScenePlan + assets + audio + captions | Timeline |
| Render | RenderJob | FinalVideo |
| Quality | FinalVideo + MediaMetadata | QualityReport |

## Agent contracts

`ResearchAgent`: ContentRequest → ResearchResult

`IdeaAgent`: ContentRequest + ResearchResult → list[ContentIdea]

`Concept selection`: list[ContentIdea] → SelectedConcept

`ScriptAgent`: ContentRequest + SelectedConcept → Script

`SceneDirector`: Script → ScenePlan

`VisualAgent`: Scene → VisualGenerationRequest → MediaAsset through VisualProvider

`VoiceAgent`: text/voice request → VoiceAsset through VoiceProvider

`TranscriptionAgent`: VoiceAsset → Transcript through TranscriptionProvider

`CaptionAgent`: Transcript + timeline context → CaptionTrack

`TimelineBuilder`: ScenePlan + MediaAssets + VoiceAsset + CaptionTrack → Timeline

`RenderAdapter`: RenderJob → FinalVideo

`QualityAgent`: FinalVideo + MediaInspector result → QualityReport

## Contract rules

1. Do not use untyped `Dict[str, Any]` as an inter-agent contract.
2. Provider-specific options belong behind provider interfaces.
3. Agent code must depend on interfaces and domain contracts, never concrete vendors.
4. Key outputs are immutable and carry `schema_version`.
5. Cache identity includes `prompt_version` so prompt changes cannot silently reuse
   incompatible generated results.
6. PHASE 0.1 does not implement concrete agents, providers, CLI, UI, or rendering.
