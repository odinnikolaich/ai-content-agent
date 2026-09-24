from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Callable

from core.models import ContentRequest
from pipeline.universal import build_scene_plan, build_script, build_visual_requests, manifest_for, save_plan
from providers.real.edge_tts_voice import EdgeTTSVoiceProvider
from providers.real.ollama_planner import OllamaPlanner
from providers.real.pollinations_image import PollinationsImageProvider

Progress = Callable[[str], None] | None

def _audio_duration(ffmpeg: str, path: Path) -> float:
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], text=True, capture_output=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        raise RuntimeError("Could not determine generated speech duration")
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

def _caption_segments(text: str, actual: float) -> list[dict[str, float | str]]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()] or [text.strip()]
    weights = [max(1, len(s.split())) for s in sentences]
    total = sum(weights)
    out=[]; cursor=0.0
    for i,(sentence,weight) in enumerate(zip(sentences,weights)):
        end = actual if i == len(sentences)-1 else cursor + actual*weight/total
        out.append({"start":round(cursor,3),"end":round(end,3),"text":sentence})
        cursor=end
    return out

def generate_video(prompt: str, duration: int = 50, voice: str | None = None,
                   llm_model: str | None = None, progress: Progress = None) -> Path:
    if not prompt.strip():
        raise ValueError("Prompt is empty")
    duration = max(43, min(int(duration), 60))
    root = Path(__file__).resolve().parents[2]
    voice = voice or os.getenv("AI_AGENT_VOICE", "ru-RU-DmitryNeural")
    llm_model = llm_model or os.getenv("AI_AGENT_LLM_MODEL", "qwen3:0.6b")
    request = ContentRequest(project_id=f"video-{uuid.uuid4().hex[:10]}", topic=prompt.strip(), duration_seconds=duration)
    work = root/"workspace"/"projects"/request.project_id
    public = root/"remotion"/"public"/"assets"/request.project_id
    work.joinpath("images").mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    def p(msg: str):
        if progress: progress(msg)

    p("🧠 Сценарий и Quality Gate")
    planner = OllamaPlanner(model=llm_model)
    script = build_script(request.topic, request.duration_seconds, planner)
    plan = build_scene_plan(script, request, planner)
    save_plan(root, request, script, plan)

    p("🎨 Визуалы")
    provider = PollinationsImageProvider(work/"images")
    assets=[]
    for i, vr in enumerate(build_visual_requests(plan, request), 1):
        filename=f"scene_{i:02d}.jpg"
        image=work/"images"/filename
        if not image.exists():
            image=provider.generate(vr.prompt, filename, request.width, request.height, 1000+i)
        shutil.copy2(image, public/filename)
        scene=plan.scenes[i-1]
        assets.append({"title":scene.on_screen_text,"image":f"{request.project_id}/{filename}",
                       "start":scene.start_seconds,"end":scene.end_seconds})

    p("🎙 Русская озвучка")
    narration=" ".join(s.narration for s in script.segments)
    audio=EdgeTTSVoiceProvider(voice).generate(narration, work/"voice_ru.mp3")
    shutil.copy2(audio, public/"voice_ru.mp3")
    ffmpeg=__import__("imageio_ffmpeg").get_ffmpeg_exe()
    actual=_audio_duration(ffmpeg,audio)
    if not 43.0 <= actual <= 60.0:
        raise RuntimeError(f"Generated speech duration is {actual:.2f}s; required range is 43–60s.")

    p("📝 Субтитры и таймлайн")
    captions=_caption_segments(narration,actual)
    manifest=manifest_for(script,plan,request,assets,f"{request.project_id}/voice_ru.mp3",captions,actual)
    (public/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")

    p("🎬 Remotion")
    output=root/"output"/f"{request.project_id}.mp4"
    npm_cmd=os.getenv("NPM_CMD") or str(Path(os.getenv("ProgramFiles","C:/Program Files"))/"nodejs"/"npm.cmd")
    subprocess.run([npm_cmd,"run","render","--","RealVertical",str(output),"--props",json.dumps(manifest,ensure_ascii=False)],
                   cwd=root/"remotion",check=True)
    p("✅ Видео готово")
    return output
