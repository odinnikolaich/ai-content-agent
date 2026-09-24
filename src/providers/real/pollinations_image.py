from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


class PollinationsImageProvider:
    """Real image-generation adapter using Pollinations."""
    def __init__(self, output_dir: Path, model: str = "flux", timeout: int = 180) -> None:
        self.output_dir = Path(output_dir)
        self.model = model
        self.timeout = timeout
        self.base_url = os.getenv("AI_AGENT_IMAGE_BASE_URL", "https://image.pollinations.ai/prompt/")

    def generate(self, prompt: str, filename: str, width: int = 1024, height: int = 1792, seed: int = -1) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        target = self.output_dir / filename
        params = f"?model={quote(self.model)}&width={width}&height={height}&seed={seed}&nologo=true&enhance=true"
        url = self.base_url.rstrip("/") + "/" + quote(prompt, safe="") + params
        headers = {"User-Agent": "AI-Content-Agent/1.0"}
        api_key = os.getenv("POLLINATIONS_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        last_error = None
        for attempt in range(3):
            try:
                req = Request(url, headers=headers)
                with urlopen(req, timeout=self.timeout) as response:
                    data = response.read()
                if len(data) < 10_000:
                    raise RuntimeError(f"image response too small: {len(data)} bytes")
                target.write_bytes(data)
                return target
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Pollinations image generation failed: {last_error}") from last_error
