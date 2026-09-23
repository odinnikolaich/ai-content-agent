# PHASE 0.1 — Architecture Review & Corrections

## Objective

Review the PHASE 0 foundation already present in this repository and correct the remaining architecture issues before PHASE 1. Do not implement PHASE 1.

## Required corrections

1. Replace untyped inter-agent contracts such as `Dict[str, Any]` with explicit domain contracts, especially `ResearchResult`.
2. Change `Script → SceneDirector → Script (updated)` to `Script → ScenePlan` so Script is not mutated by scene planning.
3. Separate VisualAgent orchestration from `VisualProvider`: VisualAgent creates a typed generation request and receives `MediaAsset` through the provider abstraction.
4. Separate Voice, transcription and captions: `VoiceAgent → VoiceAsset`, `TranscriptionProvider → Transcript`, `CaptionAgent → CaptionTrack`.
5. Introduce `MediaInspector` as a core interface. QualityAgent must depend on that interface, not directly on FFmpeg.
6. Keep paid providers optional. Do not make OpenAI, ElevenLabs, Runway or another vendor an architectural dependency.
7. Include `prompt_version` in the cache-key contract.
8. Document immutability/versioning for stage outputs such as ContentRequest, ResearchResult, SelectedConcept, Script and ScenePlan.
9. Keep the architecture compatible with mock mode and the target weak-PC environment.

## Rules

- Do not connect real APIs.
- Do not implement the full agents.
- Do not implement CLI, UI or production Remotion rendering.
- Do not begin PHASE 1.
- Preserve existing architecture unless a change is required by the corrections above.

## Acceptance criteria

- No `Dict[str, Any]` as a primary inter-agent contract.
- Scene planning produces `ScenePlan` without mutating `Script`.
- VisualProvider, TranscriptionProvider and MediaInspector abstractions are explicit.
- QualityAgent has no direct FFmpeg dependency.
- Paid vendors remain optional implementations.
- Cache contract includes prompt version.
- Documentation is internally consistent.

## Completion report

End with:

`PHASE 0.1 COMPLETED`

List changed files, architectural corrections, remaining risks and confirm:

`PHASE 1 NOT STARTED`
