# AI Content Agent

Universal local-first pipeline for turning any user prompt into a 43–60 second vertical social video.

## Production flow

user prompt → generated script → automatic scene plan → AI visuals → Russian neural voice → timed subtitles → Remotion render → MP4

The production pipeline is topic-agnostic. No particular niche is embedded in the implementation.

## Defaults

- Russian
- 9:16
- 1080×1920
- 30 FPS
- 43–60 seconds
- Real visuals through the configured image provider
- Russian speech through Edge TTS
- Remotion for composition and subtitles
- Mock mode remains available for architecture tests

## Install

python -m venv .venv
python -m pip install -U pip
python -m pip install -r requirements.txt

Then install Remotion dependencies:

cd remotion
npm install
cd ..

## Run any prompt

python scripts/run_pipeline.py "Любая тема, которую нужно объяснить или показать" --duration 50

The command creates a generated plan under workspace/projects and the final MP4 under output.

The topic is supplied only at runtime. It is not hardcoded in the production pipeline.

## Free operation

The default image adapter uses the configured Pollinations image endpoint. Edge TTS uses the Edge online speech service through edge-tts. No paid API subscription is mandatory by the pipeline architecture.

## Architecture

The planner accepts only the runtime prompt. Providers are replaceable. Remotion consumes a generic timeline manifest and does not know the subject domain.

## Tests

python -m pytest

## License

MIT
