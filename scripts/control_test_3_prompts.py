import json
from pathlib import Path

from src.pipeline.ai_guardrails import validate_plan
from src.pipeline.universal import _fallback_segments
from src.providers.real.ollama_planner import OllamaPlanner

topics = [
    "объясни квантовую запутанность",
    "сделай ролик про путешествие в Японию",
    "5 ошибок при ремонте",
]
planner = OllamaPlanner()
results = []

for topic in topics:
    print("RUNNING:", topic, flush=True)
    item = {"topic": topic}
    try:
        raw = planner.plan(topic)
        ok, errors = validate_plan(raw, topic)
        item["ai_plan"] = raw
        item["quality_gate_pass"] = ok
        item["quality_gate_errors"] = errors
        item["selected_mode"] = "ai_validated" if ok else "deterministic_fallback"
        fb = _fallback_segments(topic, 43)
        item["fallback"] = [
            {
                "segment_id": s.segment_id,
                "narration": s.narration,
                "on_screen_text": s.on_screen_text,
                "duration_seconds": s.duration_seconds,
            }
            for s in fb
        ]
        item["selected_script"] = raw.get("scenes", []) if ok else item["fallback"]
        print("DONE:", topic, "GATE=", ok, "ERRORS=", errors, flush=True)
    except Exception as e:
        fb = _fallback_segments(topic, 43)
        item["quality_gate_pass"] = False
        item["quality_gate_errors"] = ["planner_error", type(e).__name__]
        item["error"] = str(e)
        item["selected_mode"] = "deterministic_fallback"
        item["fallback"] = [
            {
                "segment_id": s.segment_id,
                "narration": s.narration,
                "on_screen_text": s.on_screen_text,
                "duration_seconds": s.duration_seconds,
            }
            for s in fb
        ]
        item["selected_script"] = item["fallback"]
        print("FALLBACK:", topic, type(e).__name__, flush=True)
    results.append(item)

Path("output").mkdir(exist_ok=True)
Path("output/control_test_3_prompts.json").write_text(
    json.dumps({"results": results}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("CONTROL_TEST_DONE", flush=True)
