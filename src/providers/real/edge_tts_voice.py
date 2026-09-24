from __future__ import annotations

import asyncio
from pathlib import Path
import edge_tts


class EdgeTTSVoiceProvider:
    """Russian neural speech through Edge TTS."""
    def __init__(self, voice: str = "ru-RU-DmitryNeural", rate: str = "+0%", volume: str = "+0%") -> None:
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def _synthesize(self, text: str, output: Path) -> None:
        await edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate, volume=self.volume).save(str(output))

    def generate(self, text: str, output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        asyncio.run(self._synthesize(text, output))
        if not output.exists() or output.stat().st_size < 1000:
            raise RuntimeError("Edge TTS returned no usable audio")
        return output
