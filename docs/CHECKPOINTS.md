# Checkpoints and Recovery

Each project stores stage state under:

```
projects/<project_id>/.state/
```

A checkpoint should contain project_id, stage, status, schema_version, application_version, timestamps, input/output references and error metadata when relevant.

Writes must be atomic: write to a temporary file, flush/close it, then rename into place. Recovery ignores incomplete temporary files and validates schema/version before loading.

Resume must be deterministic: load the latest valid completed stage and continue with the next stage. If the checkpoint is incompatible, fail with a clear CheckpointError rather than silently guessing.
