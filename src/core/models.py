"""Immutable domain contracts for PHASE 0.1.

These contracts define stage boundaries without binding the domain layer to
providers, HTTP clients, FFmpeg, Remotion, or external services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, TypeAlias


JSONValue: TypeAlias = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

SCHEMA_VERSION = "1.0"
MIN_DURATION_SECONDS = 43
MAX_DURATION_SECONDS = 60


@dataclass(frozen=True)
class ContentRequest:
    project_id: str
    topic: str
    duration_seconds: int = 50
    language: str = "ru"
    aspect_ratio: str = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
        if not self.topic.strip():
            raise ValueError("topic must not be empty")
        if not MIN_DURATION_SECONDS <= self.duration_seconds <= MAX_DURATION_SECONDS:
            raise ValueError(
                f"duration_seconds must be between {MIN_DURATION_SECONDS} and "
                f"{MAX_DURATION_SECONDS}"
            )


@dataclass(frozen=True)
class ResearchSource:
    title: str
    url: str
    source_type: str = "web"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class ResearchResult:
    topic: str
    facts: tuple[str, ...] = ()
    trends: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    sources: tuple[ResearchSource, ...] = ()
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class ContentIdea:
    idea_id: str
    title: str
    hook: str
    summary: str
    angle: str = ""
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class SelectedConcept:
    idea_id: str
    title: str
    hook: str
    summary: str
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class ScriptSegment:
    segment_id: str
    narration: str
    on_screen_text: str = ""
    duration_seconds: float = 0.0
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class Script:
    title: str
    hook: str
    segments: tuple[ScriptSegment, ...]
    total_duration_seconds: float
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class Scene:
    scene_id: str
    segment_id: str
    start_seconds: float
    end_seconds: float
    visual_direction: str
    on_screen_text: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.end_seconds < self.start_seconds:
            raise ValueError("scene end_seconds must be >= start_seconds")


@dataclass(frozen=True)
class ScenePlan:
    scenes: tuple[Scene, ...]
    total_duration_seconds: float
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class VisualGenerationRequest:
    scene_id: str
    prompt: str
    media_type: str = "image"
    duration_seconds: float = 0.0
    aspect_ratio: str = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    prompt_version: str = "1"
    parameters: Mapping[str, JSONValue] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    uri: str
    media_type: str
    duration_seconds: float = 0.0
    width: int | None = None
    height: int | None = None
    fps: int | None = None
    checksum: str | None = None
    provider: str = "unknown"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class VoiceAsset:
    asset_id: str
    uri: str
    language: str
    duration_seconds: float
    provider: str = "unknown"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class TranscriptSegment:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class Transcript:
    segments: tuple[TranscriptSegment, ...]
    language: str = "ru"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class Caption:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class CaptionTrack:
    captions: tuple[Caption, ...]
    format: str = "srt"
    language: str = "ru"
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class Timeline:
    duration_seconds: float
    scenes: tuple[Scene, ...]
    media_assets: tuple[MediaAsset, ...] = ()
    voice_assets: tuple[VoiceAsset, ...] = ()
    caption_track: CaptionTrack | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class RenderJob:
    job_id: str
    timeline: Timeline
    output_uri: str
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class MediaMetadata:
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec: str | None = None
    audio_present: bool = False
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    checks: Mapping[str, bool]
    issues: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class FinalVideo:
    uri: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    quality_report: QualityReport | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class CacheKey:
    stage: str
    input_hash: str
    provider: str = "default"
    model: str = "default"
    parameters_hash: str = ""
    prompt_version: str = "1"
    schema_version: str = SCHEMA_VERSION

    @property
    def value(self) -> str:
        parts = (
            self.stage,
            self.input_hash,
            self.provider,
            self.model,
            self.parameters_hash,
            self.prompt_version,
            self.schema_version,
        )
        return ":".join(parts)
