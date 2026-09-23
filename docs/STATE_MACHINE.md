# State Machine

States: CREATED, VALIDATING, RESEARCHING, GENERATING_IDEAS, SELECTING_CONCEPT, WRITING_SCRIPT, BUILDING_SCENES, GENERATING_VISUALS, GENERATING_AUDIO, GENERATING_CAPTIONS, BUILDING_TIMELINE, RENDERING, QUALITY_CHECK, COMPLETED, FAILED.

Rules:

- Only the orchestrator may advance pipeline state.
- State transitions are validated against an explicit transition table.
- Successful stage completion creates a checkpoint.
- Retryable errors repeat the current stage with bounded exponential backoff.
- Non-retryable errors transition to FAILED.
- Resume loads the latest valid checkpoint and continues from the next required stage.
- A checkpoint must contain enough versioned metadata to identify the stage contract and application version.
