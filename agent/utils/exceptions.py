"""Custom exceptions for the Stock Analysis Agent."""


class AgentException(Exception):
    """Base exception for agent errors."""
    pass


class ConfigurationError(AgentException):
    """Raised when there's a configuration error."""
    pass


class ToolExecutionError(AgentException):
    """Raised when tool execution fails."""
    pass


class SkillLoadError(AgentException):
    """Raised when skill loading fails."""
    pass


class MCPConnectionError(AgentException):
    """Raised when MCP connection fails."""
    pass


class LLMError(AgentException):
    """Raised when LLM request fails."""
    pass
