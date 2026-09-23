# Pipeline

```text
CREATED
  ↓
VALIDATING
  ↓
RESEARCHING
  ↓
GENERATING_IDEAS
  ↓
SELECTING_CONCEPT
  ↓
WRITING_SCRIPT
  ↓
BUILDING_SCENES
  ↓
GENERATING_VISUALS
  ↓
GENERATING_AUDIO
  ↓
GENERATING_CAPTIONS
  ↓
BUILDING_TIMELINE
  ↓
RENDERING
  ↓
QUALITY_CHECK
  ↓
COMPLETED
```

Any unrecoverable failure transitions to FAILED. Retryable provider/infrastructure failures are retried by the pipeline layer; agents do not own retry policy.

Every successful stage writes a checkpoint before the next stage begins.

Stage contracts:

- Validation: ContentRequest → validated ContentRequest
- Research: ContentRequest → ResearchResult
- Ideas: ContentRequest + ResearchResult → ContentIdea[]
- Concept: ContentIdea[] → SelectedConcept
- Script: ContentRequest + SelectedConcept → Script
- Scenes: Script → ScenePlan
- Visuals: ScenePlan → MediaAsset[]
- Audio: scene text → VoiceAsset[]
- Captions: VoiceAsset[] → Transcript → CaptionTrack
- Timeline: ScenePlan + assets + audio + captions → Timeline
- Render: Timeline → FinalVideo
- QC: FinalVideo + inspection data → QualityReport
