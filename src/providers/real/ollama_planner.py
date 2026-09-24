from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

SYSTEM_PROMPT = '''You are a professional short-form video scriptwriter and visual director.
Return ONLY valid JSON. Create a factual, engaging Russian vertical social-video plan for 43-60 seconds.
Create 6-8 scenes. Each scene needs narration, a short on-screen title, and a concrete visual prompt.
Visual prompts must describe visible subject matter, not abstract concepts. No text, logos or watermarks.
JSON: {"title":"string","hook":"string","scenes":[{"narration":"string","on_screen_text":"string","visual_prompt":"string"}]}
'''

class OllamaPlanner:
    def __init__(self, model=None, base_url=None, timeout=90):
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
        payload = {"model": self.model, "stream": False, "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Create the complete plan for this request:\n{topic}\nReturn JSON only."},
        ], "options": {"temperature": 0.7}}
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode('utf-8'))
        content = result.get("message", {}).get("content", "")
        if not content: raise ValueError("Ollama returned an empty planner response")
        value = self._parse_json(content)
        self._last_topic = topic
        self._last_plan = value
        return value

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            value = json.loads(content)
        except json.JSONDecodeError:
            start, end = content.find("{"), content.rfind("}")
            if start < 0 or end <= start: raise ValueError("Planner response is not valid JSON")
            value = json.loads(content[start:end + 1])
        if not isinstance(value, dict) or not isinstance(value.get("scenes"), list): raise ValueError("Planner JSON does not contain scenes")
        if not 6 <= len(value["scenes"]) <= 8: raise ValueError("Planner must return 6-8 scenes")
        return value