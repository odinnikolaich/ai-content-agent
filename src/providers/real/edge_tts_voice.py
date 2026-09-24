from __future__ import annotations

import asyncio
import time
from pathlib import Path
import edge_tts


class EdgeTTSVoiceProvider:
    """Russian neural speech through Edge TTS with transient-failure retries."""

    def __init__(self, voice: str = "ru-RU-DmitryNeural", rate: str = "-12%", volume: str = "+0%") -> None:
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def _synthesize(self, text: str, output: Path) -> None:
        await edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        ).save(str(output))

    def generate(self, text: str, output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        last_error = None
        for attempt in range(3):
            try:
                if output.exists():
                    output.unlink()
                asyncio.run(self._synthesize(text, output))
                if not output.exists() or output.stat().st_size < 1000:
                    raise RuntimeError("Edge TTS returned no usable audio")
                return output
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(3)
        raise RuntimeError(f"Russian Edge TTS failed after retries: {last_error}") from last_error
