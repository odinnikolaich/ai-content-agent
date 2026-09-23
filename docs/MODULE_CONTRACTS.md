# Module Contracts

## Core domain contracts

The following typed objects are stage boundaries:

- ContentRequest
- ResearchResult
- ContentIdea
- SelectedConcept
- Script
- ScenePlan
- VisualGenerationRequest
- MediaAsset
- VoiceAsset
- Transcript
- CaptionTrack
- Timeline
- RenderJob
- QualityReport
- FinalVideo

Avoid untyped `Dict[str, Any]` as an inter-agent contract.

## Agent contracts

ResearchAgent: ContentRequest → ResearchResult
IdeaAgent: ContentRequest + ResearchResult → list[ContentIdea]
Concept selection: list[ContentIdea] → SelectedConcept
ScriptAgent: ContentRequest + SelectedConcept → Script
SceneDirector: Script → ScenePlan
VisualAgent: Scene → VisualGenerationRequest → MediaAsset through VisualProvider
VoiceAgent: text/voice request → VoiceAsset through VoiceProvider
Transcription: VoiceAsset → Transcript through TranscriptionProvider
CaptionAgent: Transcript + scene/timeline context → CaptionTrack
Timeline builder: ScenePlan + MediaAssets + VoiceAsset + CaptionTrack → Timeline
Render adapter: Timeline → RenderJob/FinalVideo
QualityAgent: Timeline + media inspection results → QualityReport

Stage outputs should be versioned or immutable where mutation would damage reproducibility.
