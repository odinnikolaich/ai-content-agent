# AI Planner safety architecture

A small local LLM is treated as an optional semantic planner, not as an authoritative writer.

Pipeline:
1. Ollama/Qwen3 proposes a structured 6-8 scene plan.
2. Ollama JSON Schema constrains the response.
3. ai_guardrails.py rejects repetition, weak visuals, topic mismatch and known nonsense patterns.
4. A failed plan or unavailable Ollama automatically enters the deterministic content compiler.
5. The compiler selects a generic archetype (explain, travel, howto, compare, generic) and produces a coherent 43-60 second script without inventing specific facts.
6. Visual generation receives validated AI directions or safe concrete scene descriptions.

Paid AI is never required.
