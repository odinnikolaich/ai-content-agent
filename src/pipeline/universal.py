from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.models import ContentRequest, Scene, ScenePlan, Script, ScriptSegment, VisualGenerationRequest

ROLES = (
    ("hook", "strong opening that immediately introduces the topic and creates curiosity"),
    ("context", "explain the basic situation, problem, or promise behind the topic"),
    ("point_1", "present the first useful point, step, fact, or perspective"),
    ("point_2", "present the second useful point, step, fact, or perspective"),
    ("detail", "show an important practical detail, nuance, example, or common mistake"),
    ("result", "show the expected result, benefit, consequence, or takeaway"),
    ("close", "finish with a concise memorable conclusion or neutral call to action"),
)

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def _topic_title(topic: str) -> str:
    topic = _clean(topic)
    return topic[:1].upper() + topic[1:] if topic else "Новая тема"

def _build_segments(topic: str, duration: int) -> tuple[ScriptSegment, ...]:
    t = _topic_title(topic)
    templates = (
        f"Разберём тему «{t}» простым языком — главное, что нужно понять с самого начала.",
        f"Сначала определим, почему тема «{t}» важна и на что стоит обратить внимание.",
        f"Первый ключевой момент — понять основные шаги, условия или принципы, которые связаны с темой «{t}».",
        f"Дальше посмотрим на практическую сторону: что обычно делают, как это происходит и где чаще всего возникают сложности.",
        f"Отдельно стоит учитывать детали и ограничения: именно они часто влияют на итоговый результат в теме «{t}».",
        f"Если выстроить действия последовательно, тема «{t}» становится понятнее, а результат — более предсказуемым.",
        "Итог простой: используйте эти принципы как основу и адаптируйте их под свою конкретную ситуацию.",
    )
    weights = (0.12, 0.14, 0.15, 0.16, 0.16, 0.14, 0.13)
    target = max(43.0, min(float(duration), 60.0))
    durations = [max(4.5, target * w) for w in weights]
    scale = target / sum(durations)
    durations = [d * scale for d in durations]
    return tuple(
        ScriptSegment(
            segment_id=f"seg_{i:02d}",
            narration=text,
            on_screen_text=(t if i == 1 else ""),
            duration_seconds=round(durations[i - 1], 3),
        )
        for i, text in enumerate(templates, 1)
    )

def build_script(topic: str, duration: int) -> Script:
    segments = _build_segments(topic, duration)
    return Script(
        title=_topic_title(topic),
        hook=segments[0].narration,
        segments=segments,
        total_duration_seconds=sum(s.duration_seconds for s in segments),
    )

def build_scene_plan(script: Script, request: ContentRequest) -> ScenePlan:
    scenes = []
    cursor = 0.0
    for segment, (_, visual_role) in zip(script.segments, ROLES):
        end = cursor + segment.duration_seconds
        visual = (
            f"Create a high-quality photorealistic vertical social-video visual about "
            f"{request.topic}. Scene role: {visual_role}. Show concrete subject matter "
            f"relevant to the topic, natural composition, credible details, cinematic lighting, "
            f"documentary realism, no text, no logos, no watermark, 9:16 portrait."
        )
        scenes.append(
            Scene(
                scene_id=segment.segment_id.replace("seg_", "scene_"),
                segment_id=segment.segment_id,
                start_seconds=round(cursor, 3),
                end_seconds=round(end, 3),
                visual_direction=visual,
                on_screen_text=segment.on_screen_text,
            )
        )
        cursor = end
    return ScenePlan(scenes=tuple(scenes), total_duration_seconds=cursor)

def build_visual_requests(plan: ScenePlan, request: ContentRequest) -> tuple[VisualGenerationRequest, ...]:
    return tuple(
        VisualGenerationRequest(
            scene_id=scene.scene_id,
            prompt=scene.visual_direction,
            duration_seconds=scene.end_seconds - scene.start_seconds,
            aspect_ratio=request.aspect_ratio,
            width=request.width,
            height=request.height,
            fps=request.fps,
        )
        for scene in plan.scenes
    )

def manifest_for(
    script: Script,
    plan: ScenePlan,
    request: ContentRequest,
    assets: list[dict[str, Any]],
    audio: str,
    captions: list[dict[str, Any]],
    actual_duration: float,
) -> dict[str, Any]:
    return {
        "topic": request.topic,
        "title": script.title,
        "duration_seconds": round(actual_duration, 3),
        "fps": request.fps,
        "width": request.width,
        "height": request.height,
        "assets": assets,
        "audio": audio,
        "captions": captions,
        "scenes": [
            {"id": s.scene_id, "start": s.start_seconds, "end": s.end_seconds, "title": s.on_screen_text}
            for s in plan.scenes
        ],
    }

def save_plan(root: Path, request: ContentRequest, script: Script, plan: ScenePlan) -> Path:
    path = root / "workspace" / "projects" / request.project_id / "plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"request": asdict(request), "script": asdict(script), "scene_plan": asdict(plan)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
