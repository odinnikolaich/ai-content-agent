from __future__ import annotations
import re
from collections import Counter
from typing import Any

STOP = {"это","как","что","для","при","или","так","его","ее","они","мы","вы","на","в","и","с","по","из","не","но","а","к","у","о","за","же","то"}

def _words(text: str) -> list[str]:
    return re.findall(r"[А-Яа-яЁёA-Za-z0-9]+", text.lower())

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def validate_plan(plan: dict[str, Any], topic: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    scenes = plan.get("scenes") if isinstance(plan, dict) else None
    if not isinstance(scenes, list) or not 6 <= len(scenes) <= 8:
        return False, ["scene_count"]
    narrations = [_norm(str(s.get("narration", ""))) for s in scenes]
    visuals = [_norm(str(s.get("visual_prompt", ""))) for s in scenes]
    if any(len(_words(x)) < 8 for x in narrations): errors.append("short_narration")
    if len(set(narrations)) < max(4, len(narrations) - 1): errors.append("repeated_narration")
    if len(set(visuals)) < max(4, len(visuals) - 1): errors.append("repeated_visuals")
    all_words = [w for n in narrations for w in _words(n) if w not in STOP]
    counts = Counter(all_words)
    if all_words and sum(v for v in counts.values() if v >= 3) / len(all_words) > 0.28: errors.append("word_loop")
    topic_words = {w for w in _words(topic) if len(w) >= 4 and w not in STOP}
    if topic_words and not (topic_words & set(_words(" ".join(narrations)))): errors.append("topic_mismatch")
    if any(len(v) < 12 for v in visuals): errors.append("weak_visual_prompt")
    joined = " ".join(narrations)
    if any(p in joined for p in ("таинств", "тайн", "разное настроение", "снимок с разным", "просто миф", "афрет", "почернение, молчание")):
        errors.append("nonsense_pattern")
    return not errors, errors
