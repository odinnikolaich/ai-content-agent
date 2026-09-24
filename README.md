# AI Content Agent

Universal local-first pipeline for turning any user prompt into a 43–60 second vertical social video.

## AI planner

The production planner first tries a local Ollama LLM. The default model is Qwen3 0.6B, chosen to keep the planner practical on a weak CPU-only PC. Qwen3 is available in small local variants including 0.6B and 1.7B. If Ollama or the model is unavailable, the pipeline automatically falls back to the deterministic planner and still produces a video.

Ollama exposes a local chat API on port 11434, so the planner does not require a paid API.

## Production flow

user prompt → local AI script + scene planning → automatic scene timing → AI visuals → Russian neural voice → timed subtitles → Remotion → MP4

The LLM produces topic-specific narration and concrete visual prompts. The old hardcoded example topic is not used by the production pipeline.

## Install

Install Ollama, then pull the small model:

ollama pull qwen3:0.6b

Python:

python -m venv .venv
python -m pip install -U pip
python -m pip install -r requirements.txt

Remotion:

cd remotion
npm install
cd ..

## Run

python scripts/run_pipeline.py "объясни квантовую запутанность" --duration 50

python scripts/run_pipeline.py "сделай ролик про путешествие в Японию" --duration 50

python scripts/run_pipeline.py "5 ошибок при ремонте" --duration 50

For a stronger local planner, try:
python scripts/run_pipeline.py "ваш запрос" --duration 50 --llm-model qwen3:1.7b

If Ollama is stopped, generation continues with the free deterministic fallback.

## Free operation

The LLM planner is local. Image generation uses the configured free image adapter and Russian voice uses Edge TTS. No paid API is mandatory.

## Tests

python -m pytest

## License

MIT
