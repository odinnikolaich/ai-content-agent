from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from core.models import ContentRequest
from providers.real.edge_tts_voice import EdgeTTSVoiceProvider
from providers.real.pollinations_image import PollinationsImageProvider

SCENES = [
("Зимнее строительство","photorealistic documentary photo, modular house construction in winter, snow-covered site, workers in safety clothing, unfinished modern modular house, cold morning light, realistic architecture photography, no text, vertical composition"),
("Подготовка участка","photorealistic construction site in winter, prepared foundation for a modular house, snow around the site, construction equipment, workers preparing the foundation, realistic documentary photography, no text, vertical composition"),
("Производство модулей","photorealistic factory interior, modern modular house modules being assembled, skilled construction workers, clean industrial workshop, realistic architectural photography, no text, vertical composition"),
("Доставка модулей","photorealistic winter construction logistics, large modular house section transported by truck to a snowy site, crane preparing installation, realistic documentary photography, no text, vertical composition"),
("Монтаж","photorealistic crane installing a prefabricated modular house section on a prepared foundation in winter, snowy landscape, workers guiding the module, realistic construction photography, no text, vertical composition"),
("Утепление и инженерия","photorealistic workers installing insulation and utilities inside a modern modular house during winter construction, detailed materials, warm work lights, realistic documentary photography, no text, vertical composition"),
("Готовый дом","photorealistic finished modern modular house in a snowy winter landscape, warm windows, clean yard, evening blue hour, realistic architectural photography, no text, vertical composition"),
]

NARRATION = (
"Можно ли строить модульный дом зимой? Да. "
"Главное — правильно подготовить участок, фундамент и логистику. "
"Большую часть модулей производят заранее в контролируемых условиях. "
"На площадке готовые секции доставляют и устанавливают с помощью крана. "
"После монтажа выполняют утепление, инженерные системы и герметизацию. "
"Зимой особенно важны защита рабочих зон и контроль технологии. "
"Также нужно заранее продумать подъезд техники, хранение материалов и защиту от снега. "
"В результате дом собирается быстро, а время работ на участке сокращается. "
"Правильная организация позволяет продолжать строительство даже в холодный сезон."
)

def audio_duration(ffmpeg: str, path: Path) -> float:
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], text=True, capture_output=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        raise RuntimeError("Could not determine generated speech duration")
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("topic", nargs="?", default="строительство модульного дома зимой")
    p.add_argument("--duration", type=int, default=43)
    p.add_argument("--voice", default=os.getenv("AI_AGENT_VOICE", "ru-RU-DmitryNeural"))
    args = p.parse_args()

    request = ContentRequest(project_id="real-demo", topic=args.topic, duration_seconds=args.duration)
    root = Path(__file__).resolve().parents[1]
    work = root/"workspace"/"projects"/"real-demo"
    public = root/"remotion"/"public"/"assets"/"real-demo"
    work.mkdir(parents=True, exist_ok=True)
    (work/"images").mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    images = PollinationsImageProvider(work/"images")
    voice = EdgeTTSVoiceProvider(args.voice)
    assets = []
    for i, (title, visual) in enumerate(SCENES, 1):
        image = work/"images"/f"scene_{i:02d}.jpg"
        if not image.exists():
            image = images.generate(f"{visual}. Topic: {args.topic}.", f"scene_{i:02d}.jpg", 1024, 1792, 100+i)
        shutil.copy2(image, public/f"scene_{i:02d}.jpg")
        assets.append({"title": title, "image": f"scene_{i:02d}.jpg"})

    audio = voice.generate(NARRATION, work/"voice_ru.mp3")
    shutil.copy2(audio, public/"voice_ru.mp3")
    ffmpeg = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    actual = audio_duration(ffmpeg, audio)
    if actual < 43:
        raise RuntimeError(f"Russian speech is only {actual:.2f}s; at least 43s is required")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", NARRATION) if s.strip()]
    step = actual / len(sentences)
    captions = [
        {"start": round(i*step, 3), "end": round((i+1)*step, 3), "text": sentence}
        for i, sentence in enumerate(sentences)
    ]
    manifest = {
        "topic": args.topic,
        "duration_seconds": request.duration_seconds,
        "fps": request.fps,
        "width": request.width,
        "height": request.height,
        "assets": assets,
        "audio": "voice_ru.mp3",
        "captions": captions,
    }
    (public/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    subprocess.run(
        ["npm", "run", "render", "--", "RealVertical", str(root/"output"/"real_demo.mp4"),
         "--props", json.dumps(manifest, ensure_ascii=False)],
        cwd=root/"remotion", check=True,
    )
    print(f"VIDEO_READY={root/'output'/'real_demo.mp4'}")
    print(f"SPEECH_DURATION={actual:.2f}")

if __name__ == "__main__":
    main()
