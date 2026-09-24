from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from core.models import ContentRequest
from pipeline.universal import build_scene_plan, build_script, build_visual_requests, manifest_for, save_plan
from providers.real.edge_tts_voice import EdgeTTSVoiceProvider
from providers.real.pollinations_image import PollinationsImageProvider

def audio_duration(ffmpeg: str, path: Path) -> float:
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], text=True, capture_output=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        raise RuntimeError("Could not determine generated speech duration")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

def caption_segments(text: str, actual: float) -> list[dict[str, float | str]]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()] or [text.strip()]
    weights = [max(1, len(s.split())) for s in sentences]
    total = sum(weights)
    captions = []
    cursor = 0.0
    for index, (sentence, weight) in enumerate(zip(sentences, weights)):
        end = actual if index == len(sentences) - 1 else cursor + actual * weight / total
        captions.append({"start": round(cursor, 3), "end": round(end, 3), "text": sentence})
        cursor = end
    return captions

def main() -> None:
    parser = argparse.ArgumentParser(description="Universal prompt-to-video pipeline")
    parser.add_argument("prompt", help="Any user topic or video request")
    parser.add_argument("--duration", type=int, default=50)
    parser.add_argument("--voice", default=os.getenv("AI_AGENT_VOICE", "ru-RU-DmitryNeural"))
    args = parser.parse_args()

    request = ContentRequest(
        project_id=f"video-{uuid.uuid4().hex[:10]}",
        topic=args.prompt,
        duration_seconds=args.duration,
    )
    root = Path(__file__).resolve().parents[1]
    work = root / "workspace" / "projects" / request.project_id
    public = root / "remotion" / "public" / "assets" / request.project_id
    work.mkdir(parents=True, exist_ok=True)
    (work / "images").mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    script = build_script(request.topic, request.duration_seconds)
    plan = build_scene_plan(script, request)
    save_plan(root, request, script, plan)
    visual_requests = build_visual_requests(plan, request)

    image_provider = PollinationsImageProvider(work / "images")
    assets = []
    for index, visual_request in enumerate(visual_requests, 1):
        filename = f"scene_{index:02d}.jpg"
        image = work / "images" / filename
        if not image.exists():
            image = image_provider.generate(
                visual_request.prompt, filename, request.width, request.height, 1000 + index
            )
        shutil.copy2(image, public / filename)
        scene = plan.scenes[index - 1]
        assets.append({
            "title": scene.on_screen_text,
            "image": filename,
            "start": scene.start_seconds,
            "end": scene.end_seconds,
        })

    narration = " ".join(segment.narration for segment in script.segments)
    audio = EdgeTTSVoiceProvider(args.voice).generate(narration, work / "voice_ru.mp3")
    shutil.copy2(audio, public / "voice_ru.mp3")

    ffmpeg = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    actual = audio_duration(ffmpeg, audio)
    if not 43.0 <= actual <= 60.0:
        raise RuntimeError(f"Generated speech duration is {actual:.2f}s; required range is 43–60s.")

    captions = caption_segments(narration, actual)
    manifest = manifest_for(script, plan, request, assets, "voice_ru.mp3", captions, actual)
    (public / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    output = root / "output" / f"{request.project_id}.mp4"
    npm_cmd = os.getenv("NPM_CMD") or str(Path(os.getenv("ProgramFiles", "C:/Program Files")) / "nodejs" / "npm.cmd")
    subprocess.run(
        [npm_cmd, "run", "render", "--", "RealVertical", str(output), "--props", json.dumps(manifest, ensure_ascii=False)],
        cwd=root / "remotion",
        check=True,
    )
    print(f"VIDEO_READY={output}")
    print(f"SPEECH_DURATION={actual:.2f}")
    print(f"PLAN={work / 'plan.json'}")

if __name__ == "__main__":
    main()
