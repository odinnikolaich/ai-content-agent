from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.models import ContentRequest, Scene, ScenePlan, Script, ScriptSegment, VisualGenerationRequest
from pipeline.ai_guardrails import validate_plan
from providers.real.ollama_planner import OllamaPlanner

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip())

def _kind(topic: str) -> str:
    t = topic.lower()
    if any(x in t for x in ("ошиб", "совет", "правил", "способ", "шаг", "как ", "ремонт", "строитель")):
        return "howto"
    if any(x in t for x in ("путеше", "япони", "отпуск", "маршрут", "куда поехать")):
        return "travel"
    if any(x in t for x in ("почему", "объясни", "как работает", "квант", "наука", "физик", "истори")):
        return "explain"
    if any(x in t for x in ("обзор", "сравни", "выбрать", "лучший", "топ")):
        return "compare"
    return "generic"

def _fallback_segments(topic: str, duration: int) -> tuple[ScriptSegment, ...]:
    t = _clean(topic)
    kind = _kind(t)
    if kind == "explain":
        texts = [
            f"Сегодня разберём тему «{t}» простыми словами — без лишней терминологии.",
            "Сначала определим главное понятие и поймём, какие объекты или процессы здесь участвуют.",
            "Затем посмотрим на механизм: что происходит по шагам и почему результат получается именно таким.",
            "Важно отделить реальный принцип от популярных упрощений, которые часто искажают смысл.",
            "Теперь свяжем идею с практикой: где этот принцип можно увидеть или применить.",
            f"Если свести всё к одной мысли, тема «{t}» становится понятнее, когда мы видим связь между причиной, процессом и результатом.",
            "Сохраните ролик, если хотите вернуться к объяснению позже.",
        ]
    elif kind == "travel":
        texts = [
            f"Планируем путешествие по теме «{t}»: сначала определяем цель поездки и доступное время.",
            "Дальше выбираем базовый маршрут: несколько ключевых мест лучше распределить по дням, а не пытаться увидеть всё сразу.",
            "Отдельно закладываем время на дорогу, пересадки и непредвиденные задержки.",
            "Для бюджета заранее разделяем жильё, транспорт, питание и платные активности.",
            "Перед поездкой проверяем документы, правила въезда, связь, оплату и прогноз погоды.",
            "Главный принцип прост: меньше точек в расписании — больше времени на саму поездку.",
            "Сохраните план, чтобы использовать его при подготовке следующего маршрута.",
        ]
    elif kind == "howto":
        texts = [
            f"Разберём тему «{t}» через типичные ошибки, которые можно предотвратить ещё до начала работы.",
            "Ошибка номер один — начинать без плана: сначала определите результат, порядок действий и необходимые материалы.",
            "Ошибка номер два — экономить на подготовке: исправление проблем после начала работы обычно занимает больше времени.",
            "Ошибка номер три — пропускать промежуточную проверку качества вместо контроля каждого этапа.",
            "Ошибка номер четыре — ориентироваться только на внешний вид и забывать о скрытых причинах проблемы.",
            "Ошибка номер пять — не оставлять запас по времени и бюджету на непредвиденные ситуации.",
            f"Если применить эти правила к теме «{t}», работа становится предсказуемее и требует меньше переделок.",
        ]
    elif kind == "compare":
        texts = [
            f"Разберём тему «{t}» через понятные критерии, чтобы сравнение было не по одному признаку.",
            "Сначала определяем главную задачу: разные варианты могут быть удобны для разных целей.",
            "Затем сравниваем стоимость, время, сложность и требования к обслуживанию.",
            "Следующий критерий — ограничения: доступное пространство, ресурсы, опыт и условия использования.",
            "После этого смотрим на долгосрочные последствия, а не только на цену или эффект в первый день.",
            "И наконец, проверяем, какой компромисс каждый вариант предлагает между удобством и затратами.",
            "Такой подход помогает выбрать вариант под конкретную задачу, а не под универсальный рейтинг.",
        ]
    else:
        texts = [
            f"Сегодня коротко и по делу разберём тему «{t}».",
            "Сначала определим главный вопрос: что именно нужно понять или получить в результате.",
            "Затем разложим тему на несколько простых частей и посмотрим на каждую отдельно.",
            "Следующий шаг — проверить, какие факторы действительно влияют на результат.",
            "Отдельно отметим распространённую ошибку: не стоит делать вывод по одному признаку.",
            "После этого соберём всё в практический вывод, который можно применить к исходной задаче.",
            f"Главная мысль темы «{t}» — действовать последовательно, проверяя результат на каждом этапе.",
        ]
    target = max(43.0, min(float(duration), 60.0))
    weights = [max(1, len(x.split())) for x in texts]
    total = sum(weights)
    durations = [target * w / total for w in weights]
    return tuple(ScriptSegment(f"seg_{i:02d}", text, _on_screen(i, kind), round(durations[i - 1], 3)) for i, text in enumerate(texts, 1))

def _on_screen(index: int, kind: str) -> str:
    labels = {
        "explain": ["Главная идея", "Понятие", "Механизм", "Что важно", "Применение", "Итог", "Запомните"],
        "travel": ["Цель поездки", "Маршрут", "Время", "Бюджет", "Подготовка", "Главный принцип", "Сохраните"],
        "howto": ["Главная ошибка", "Ошибка №1", "Ошибка №2", "Ошибка №3", "Ошибка №4", "Ошибка №5", "Итог"],
        "compare": ["Критерии", "Задача", "Стоимость", "Ограничения", "Долгий срок", "Компромисс", "Вывод"],
        "generic": ["Тема", "Вопрос", "Части", "Факторы", "Ошибка", "Практика", "Итог"],
    }
    return labels.get(kind, labels["generic"])[index - 1]

def _script_from_ai(data: dict[str, Any], topic: str, duration: int) -> Script | None:
    ok, _ = validate_plan(data, topic)
    if not ok:
        return None
    scenes = data["scenes"]
    target = max(43.0, min(float(duration), 60.0))
    weights = [max(1, len(_clean(s["narration"]).split())) for s in scenes]
    total = sum(weights)
    durations = [target * w / total for w in weights]
    segments = tuple(ScriptSegment(f"seg_{i:02d}", _clean(s["narration"]), _clean(s.get("on_screen_text", "")), round(durations[i - 1], 3)) for i, s in enumerate(scenes, 1))
    return Script(_clean(data.get("title") or topic), segments[0].narration, segments, sum(x.duration_seconds for x in segments))

def build_script(topic: str, duration: int, planner: OllamaPlanner | None = None) -> Script:
    planner = planner or OllamaPlanner()
    try:
        if planner.available():
            result = _script_from_ai(planner.plan(topic), topic, duration)
            if result is not None:
                return result
    except Exception:
        pass
    segments = _fallback_segments(topic, duration)
    return Script(_clean(topic), segments[0].narration, segments, sum(x.duration_seconds for x in segments))

def build_scene_plan(script: Script, request: ContentRequest, planner: OllamaPlanner | None = None) -> ScenePlan:
    visuals: list[str] = []
    try:
        if planner and planner.available():
            data = planner.plan(request.topic)
            ok, _ = validate_plan(data, request.topic)
            if ok:
                visuals = [_clean(s.get("visual_prompt", "")) for s in data["scenes"]]
    except Exception:
        visuals = []
    scenes = []
    cursor = 0.0
    for i, segment in enumerate(script.segments):
        end = cursor + segment.duration_seconds
        visual = visuals[i] if i < len(visuals) and visuals[i] else f"Photorealistic vertical documentary scene. Show a concrete visible subject or action illustrating: {segment.narration}. Natural lighting, realistic details, no text, logos or watermark, 9:16."
        scenes.append(Scene(segment.segment_id.replace("seg_", "scene_"), segment.segment_id, round(cursor, 3), round(end, 3), visual, segment.on_screen_text))
        cursor = end
    return ScenePlan(tuple(scenes), cursor)

def build_visual_requests(plan: ScenePlan, request: ContentRequest) -> tuple[VisualGenerationRequest, ...]:
    return tuple(VisualGenerationRequest(s.scene_id, s.visual_direction, duration_seconds=s.end_seconds-s.start_seconds, aspect_ratio=request.aspect_ratio, width=request.width, height=request.height, fps=request.fps) for s in plan.scenes)

def manifest_for(script: Script, plan: ScenePlan, request: ContentRequest, assets: list[dict[str, Any]], audio: str, captions: list[dict[str, Any]], actual_duration: float) -> dict[str, Any]:
    return {"topic": request.topic, "title": script.title, "duration_seconds": round(actual_duration, 3), "fps": request.fps, "width": request.width, "height": request.height, "assets": assets, "audio": audio, "captions": captions, "scenes": [{"id": s.scene_id, "start": s.start_seconds, "end": s.end_seconds, "title": s.on_screen_text} for s in plan.scenes]}

def save_plan(root: Path, request: ContentRequest, script: Script, plan: ScenePlan) -> Path:
    path = root / "workspace" / "projects" / request.project_id / "plan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"request": asdict(request), "script": asdict(script), "scene_plan": asdict(plan)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
