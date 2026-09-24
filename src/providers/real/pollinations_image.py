from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont


class PollinationsImageProvider:
    """Real image-generation adapter using Pollinations, with local fallback."""

    def __init__(self, output_dir: Path, model: str = "flux", timeout: int = 20) -> None:
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
        for attempt in range(1):
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

        try:
            image = Image.new(
                "RGB",
                (width, height),
                tuple(25 + (b % 45) for b in hashlib.sha256(prompt.encode("utf-8")).digest()[:3]),
            )
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()
            draw.text((60, 80), "LOCAL VISUAL FALLBACK", font=font, fill="white")
            words = prompt.split()
            line = ""
            y = height // 2 - 60
            for word in words:
                test = (line + " " + word).strip()
                if len(test) > 28:
                    draw.text((60, y), line, font=font, fill="white")
                    y += 35
                    line = word
                else:
                    line = test
            if line:
                draw.text((60, y), line, font=font, fill="white")
            image.save(target, "JPEG", quality=94)
            return target
        except Exception:
            raise RuntimeError(f"Pollinations image generation failed: {last_error}") from last_error
