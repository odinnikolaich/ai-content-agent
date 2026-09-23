# Checkpoints and Recovery

Each project stores stage state under:

```
projects/<project_id>/.state/
```

## Checkpoint contract

A checkpoint must contain:

- `project_id`
- `stage`
- `status`
- `schema_version`
- `application_version`
- creation/update timestamps
- input reference
- output reference
- error metadata when relevant

Stage outputs referenced by checkpoints are immutable/versioned artifacts.

## Cache identity

Generated artifacts must not be keyed only by topic or prompt text. The cache
identity must include:

- stage
- input hash
- provider
- model
- provider-parameter hash
- `prompt_version`
- `schema_version`

Changing the prompt version therefore invalidates incompatible cached results.

## Atomic writes

Write checkpoint data to a temporary file, flush/close it, then atomically rename
it into place. Recovery ignores incomplete temporary files.

## Resume

Resume loads the latest valid completed stage and continues with the next stage.
The loader must validate the checkpoint schema before accepting it.

An incompatible or corrupt checkpoint raises `CheckpointError`; the system must
not silently guess or rebuild state.

## PHASE 0.1 boundary

This document defines the contract only. Checkpoint persistence, locking,
recovery implementation, and pipeline orchestration are not implemented until
their respective later phases.
