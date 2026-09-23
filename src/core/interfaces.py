"""Provider and infrastructure contracts.

Agents depend on these protocols rather than concrete vendor implementations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from .models import (
    CaptionTrack,
    FinalVideo,
    MediaAsset,
    MediaMetadata,
    RenderJob,
    ResearchResult,
    Timeline,
    Transcript,
    VoiceAsset,
    VisualGenerationRequest,
)


class LLMProvider(Protocol):
    async def generate(self, prompt: str, *, model: str | None = None) -> str: ...


class ImageProvider(Protocol):
    async def generate(self, request: VisualGenerationRequest) -> MediaAsset: ...


class VideoProvider(Protocol):
    async def generate(self, request: VisualGenerationRequest) -> MediaAsset: ...


class VisualProvider(Protocol):
    async def generate(self, request: VisualGenerationRequest) -> MediaAsset: ...


class VoiceProvider(Protocol):
    async def synthesize(
        self,
        text: str,
        *,
        language: str,
        voice: str | None = None,
    ) -> VoiceAsset: ...


class TranscriptionProvider(Protocol):
    async def transcribe(self, asset: VoiceAsset) -> Transcript: ...


class StorageProvider(Protocol):
    async def save(self, source: Path, destination: str) -> str: ...

    async def load(self, uri: str, destination: Path) -> Path: ...


class MediaInspector(Protocol):
    async def inspect(self, asset: MediaAsset | Path) -> MediaMetadata: ...


class Renderer(Protocol):
    async def render(self, job: RenderJob) -> FinalVideo: ...


class ResearchProvider(Protocol):
    async def research(self, topic: str) -> ResearchResult: ...


class CaptionRenderer(Protocol):
    async def render(self, timeline: Timeline, captions: CaptionTrack) -> Timeline: ...
