# AI Content Agent

Local-first, provider-agnostic pipeline for producing short social videos.

## Status
**PHASE 2 — First executable vertical prototype**

The repository now has a provider-free end-to-end demo: prompt → scene cards → synthetic audio → SRT captions → 43–60 second vertical MP4. The mock path runs without API keys and is intended to validate the architecture on modest hardware.

This first MP4 is an integration test, not the final AI generator: visuals are deterministic cards and the audio is synthetic. Real visual generation, Russian TTS, richer captions and Remotion composition are the next stages.

## Target defaults
- Russian
- 9:16
- 1080×1920
- 30 FPS
- 43–60 seconds
- Mock providers for free local testing

## Installation
python -m venv .venv

Windows:
python -m pip install -U pip
python -m pip install -e ".[dev]"

## Run the first video
python scripts/run_demo.py

Or:
python scripts/run_demo.py "строительство модульного дома зимой" --duration 43

Output: output/demo_<hash>.mp4

## Testing
python -m pytest

See docs/PHASE_2.md for details.

## Roadmap
PHASE 0 → PHASE 0.1 → PHASE 1 → PHASE 2 executable prototype → PHASE 3 real/free providers → PHASE 4 agents → PHASE 5 Remotion → PHASE 6 voice/captions → PHASE 7 QC → PHASE 8 CLI → PHASE 9 API → PHASE 10 optimization

## License
MIT
