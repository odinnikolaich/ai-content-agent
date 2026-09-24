# PHASE 2 — First Executable Vertical Prototype

PHASE 2 proves the end-to-end shape of the product without paid APIs.

## What it does

A prompt is converted into a validated ContentRequest, seven deterministic vertical scene cards, a 43–60 second synthetic audio track, an SRT caption track, and an MP4 assembled with FFmpeg through imageio-ffmpeg.

The visual and audio providers are deliberately MOCK implementations. This is not yet AI-generated footage or Russian speech. It is a runnable integration harness that lets us verify the pipeline on the target PC before adding heavy AI models.

## Run

python -m pip install -e ".[dev]"
python scripts/run_demo.py

Custom prompt:

python scripts/run_demo.py "строительство модульного дома зимой" --duration 43

The MP4 is written to output/. Intermediate PNG cards, WAV audio and SRT captions are stored under workspace/projects/demo/mock/.

## Next

Replace the mock visual and voice stages with provider adapters, while keeping the same domain contracts and CLI. Remotion can then become the richer composition layer without changing the provider-facing architecture.
