from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.models import ContentRequest, Scene, ScenePlan, Script, ScriptSegment, VisualGenerationRequest
from providers.real.ollama_planner import OllamaPlanner

def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', str(text).strip())

def _fallback_segments(topic: str, duration: int) -> tuple[ScriptSegment, ...]:
    t = _clean(topic)
    templates = (
        f'Разберём тему «{t}» простым языком — главное, что нужно понять с самого начала.',
        f'Сначала определим, почему тема «{t}» важна и на что стоит обратить внимание.',
        f'Первый ключевой момент — понять основные шаги, условия или принципы, связанные с темой «{t}».',
        f'Дальше посмотрим на практическую сторону: что происходит на практике и где чаще всего возникают сложности.',
        'Отдельно стоит учитывать детали и ограничения: именно они могут заметно повлиять на результат.',
        f'Если выстроить действия последовательно, тема «{t}» становится понятнее, а результат — предсказуемее.',
        'Итог простой: используйте эти принципы как основу и адаптируйте их под свою ситуацию.',
    )
    weights = (0.12, 0.14, 0.15, 0.16, 0.16, 0.14, 0.13)
    target = max(43.0, min(float(duration), 60.0))
    durations = [target * w for w in weights]
    return tuple(ScriptSegment(f'seg_{i:02d}', text, t if i == 1 else '', round(durations[i-1], 3)) for i, text in enumerate(templates, 1))

def build_script(topic: str, duration: int, planner: OllamaPlanner | None = None) -> Script:
    planner = planner or OllamaPlanner()
    try:
        if planner.available():
            data = planner.plan(topic)
            scenes = [s for s in data['scenes'] if _clean(s.get('narration'))]
            if len(scenes) >= 6:
                target = max(43.0, min(float(duration), 60.0))
                weights = [max(1, len(_clean(s['narration']).split())) for s in scenes]
                total = sum(weights)
                durations = [target * w / total for w in weights]
                segments = tuple(ScriptSegment(f'seg_{i:02d}', _clean(s['narration']), _clean(s.get('on_screen_text', '')), round(durations[i-1], 3)) for i, s in enumerate(scenes, 1))
                return Script(_clean(data.get('title') or topic), segments[0].narration, segments, sum(x.duration_seconds for x in segments))
    except Exception:
        pass
    segments = _fallback_segments(topic, duration)
    return Script(_clean(topic), segments[0].narration, segments, sum(x.duration_seconds for x in segments))

def build_scene_plan(script: Script, request: ContentRequest, planner: OllamaPlanner | None = None) -> ScenePlan:
    visuals = []
    try:
        if planner and planner.available():
            data = planner.plan(request.topic)
            visuals = [_clean(s.get('visual_prompt', '')) for s in data['scenes']]
    except Exception:
        visuals = []
    scenes = []
    cursor = 0.0
    for i, segment in enumerate(script.segments):
        end = cursor + segment.duration_seconds
        visual = visuals[i] if i < len(visuals) and visuals[i] else f'Photorealistic vertical scene about {request.topic}. Show a concrete visible subject or action that illustrates: {segment.narration}. Documentary realism, no text, logos or watermark, 9:16.'
        scenes.append(Scene(segment.segment_id.replace('seg_', 'scene_'), segment.segment_id, round(cursor, 3), round(end, 3), visual, segment.on_screen_text))
        cursor = end
    return ScenePlan(tuple(scenes), cursor)

def build_visual_requests(plan: ScenePlan, request: ContentRequest) -> tuple[VisualGenerationRequest, ...]:
    return tuple(VisualGenerationRequest(s.scene_id, s.visual_direction, duration_seconds=s.end_seconds-s.start_seconds, aspect_ratio=request.aspect_ratio, width=request.width, height=request.height, fps=request.fps) for s in plan.scenes)

def manifest_for(script: Script, plan: ScenePlan, request: ContentRequest, assets: list[dict[str, Any]], audio: str, captions: list[dict[str, Any]], actual_duration: float) -> dict[str, Any]:
    return {'topic': request.topic, 'title': script.title, 'duration_seconds': round(actual_duration,3), 'fps': request.fps, 'width': request.width, 'height': request.height, 'assets': assets, 'audio': audio, 'captions': captions, 'scenes': [{'id':s.scene_id,'start':s.start_seconds,'end':s.end_seconds,'title':s.on_screen_text} for s in plan.scenes]}

def save_plan(root: Path, request: ContentRequest, script: Script, plan: ScenePlan) -> Path:
    path = root / 'workspace' / 'projects' / request.project_id / 'plan.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'request':asdict(request),'script':asdict(script),'scene_plan':asdict(plan)}, ensure_ascii=False, indent=2), encoding='utf-8')
    return path