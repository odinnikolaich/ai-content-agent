Remotion rendering layer

Remotion 4.0.527 is the final vertical composition layer. The universal Python pipeline generates a generic timeline manifest, real image assets, Russian speech and timed captions, then invokes Remotion.

Install in remotion/: npm install

Run the universal pipeline from the repository root:
python scripts/run_pipeline.py "любой пользовательский запрос" --duration 50

The final render is written to output/<generated-id>.mp4.

Remotion receives only generic assets, scene timing, audio and captions. It is not tied to a particular topic or niche.
