"""Exception types shared across Lily."""


class LilyError(Exception):
    """Base class: anything Lily can explain to the user."""


class ConfigError(LilyError):
    """Bad or missing configuration."""


class LLMError(LilyError):
    """The model or router could not answer."""


class ToolError(LilyError):
    """A tool failed or was refused."""
