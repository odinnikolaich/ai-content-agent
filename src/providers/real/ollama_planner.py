import json
import os
import urllib.error
import urllib.request
from typing import Any

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string"},
        "scenes": {
            "type": "array",
            "minItems": 6,
            "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "on_screen_text": {"type": "string"},
                    "visual_prompt": {"type": "string"},
                },
                "required": ["narration", "on_screen_text", "visual_prompt"],
            },
        },
    },
    "required": ["title", "hook", "scenes"],
}

SYSTEM_PROMPT = """Ты редактор коротких русскоязычных роликов.
Предложи содержательный план, но не выдумывай факты.
Пиши простыми короткими предложениями. Не повторяй одну мысль в разных сценах.
Если тема требует точных фактов, не придумывай числа, даты, имена или технические детали.
Каждая сцена должна иметь новую функцию: хук, объяснение, механизм или причина, пример, практический вывод, итог.
visual_prompt должен описывать конкретный видимый объект или действие, а не абстракцию.
Не используй слова вроде «тайна», «таинственный», «разное настроение», если они не являются частью темы.
Верни только JSON по заданной схеме."""

class OllamaPlanner:
    def __init__(self, model=None, base_url=None, timeout=300):
        self.model = model or os.getenv("AI_AGENT_LLM_MODEL", "qwen3:0.6b")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout
        self._last_topic = None
        self._last_plan = None

    def available(self) -> bool:
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{self.base_url}/api/tags"), timeout=3):
                return True
        except (OSError, urllib.error.URLError):
            return False

    def plan(self, topic: str) -> dict[str, Any]:
        if self._last_topic == topic and self._last_plan is not None:
            return self._last_plan
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": SCHEMA,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Сделай план для запроса пользователя:\n{topic}"},
            ],
            "options": {"temperature": 0.2, "top_p": 0.8, "num_predict": 650},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        content = result.get("message", {}).get("content", "")
        if not content:
            raise ValueError("Ollama returned an empty planner response")
        try:
            value = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ollama returned malformed structured output: {exc}") from exc
        if not isinstance(value, dict) or not isinstance(value.get("scenes"), list):
            raise ValueError("Planner JSON does not contain scenes")
        self._last_topic = topic
        self._last_plan = value
        return value
