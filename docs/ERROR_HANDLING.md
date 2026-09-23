# Error Handling

Retryable examples: provider timeout, rate limit, temporary network failure, transient filesystem/resource failure.

Non-retryable examples: validation error, invalid configuration, invalid prompt, incompatible checkpoint, unsupported media.

Retry policy belongs to the pipeline layer. Agents report typed errors; they do not sleep or independently retry.

Use bounded exponential backoff with configurable limits. All terminal failures must preserve enough context for diagnosis and resume/restart decisions.
