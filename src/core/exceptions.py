"""Project exception taxonomy.

Exceptions are intentionally provider-agnostic so the pipeline can classify
failures without importing vendor SDKs.
"""


class ContentAgentError(Exception):
    """Base class for all project errors."""


class DomainValidationError(ContentAgentError):
    """Input or domain-contract validation failed."""


class ConfigurationError(ContentAgentError):
    """Configuration is missing or invalid."""


class AgentError(ContentAgentError):
    """An agent failed to produce its contract output."""


class ProviderError(ContentAgentError):
    """A provider failed while fulfilling a contract."""


class ProviderTimeoutError(ProviderError):
    """A provider operation timed out and may be retried."""


class RateLimitError(ProviderError):
    """A provider rate limit was reached and may be retried."""


class TemporaryNetworkError(ProviderError):
    """A transient network error occurred and may be retried."""


class QuotaExceededError(ProviderError):
    """A provider quota was exhausted."""


class InvalidPromptError(ProviderError):
    """A provider rejected the generated request as invalid."""


class RenderingError(ContentAgentError):
    """Rendering or media assembly failed."""


class MediaInspectionError(ContentAgentError):
    """Media metadata could not be inspected reliably."""


class CheckpointError(ContentAgentError):
    """Checkpoint is invalid, incompatible, or cannot be recovered."""


class PipelineError(ContentAgentError):
    """The pipeline cannot continue from the current state."""
